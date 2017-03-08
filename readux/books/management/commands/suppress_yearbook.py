import pdb, re
from optparse import make_option
from django.core.management.base import BaseCommand, CommandError
from readux.utils import solr_interface
from django.conf import settings

class Command(BaseCommand):
    '''Utility script to suppress Emory Yearbooks post 1922. It deletes the Solr
       index so that the items will not show up in the search results in Readux.
       Items are still available but not very visible unless you know the URL.

       Can run in dry-run mode to get a summary without actually making any changes.
    '''

    option_list = BaseCommand.option_list + (
        make_option('--dry-run', '-n',
            action='store_true',
            default=False,
            help='Don\'t make any changes; just report on what would be done'),
        )

    def handle(self, **options):
        dry_run = options.get('dry_run', False)
        collection_id = "emory-control:LSDI-EmoryYearbooks"
        year_threadhold = 1922
        solr = solr_interface()
        resp = solr.query(collection_id=collection_id).execute()

        # Announcements
        print "\n"
        print "###################### Important ######################"
        if dry_run: print "*********************** DRY RUN ***********************"
        print "environmental varaibles configured as follows"
        print "collection_id to match: {}".format(collection_id)
        print "year threshold: {} (not including {})".format(year_threadhold, year_threadhold)
        print "solr env: {}".format(settings.SOLR_SERVER_URL)
        print "#######################################################"
        print "\n"

        # When there are results returned
        if len(resp) > 0:
            summary = [] # store index to be purged

            # Print summary on top
            print "Records with collection_id {} found: {}, listing: ".format(collection_id, len(resp))

            # Regex to match "_yyyy"
            regex = r"(\_\d{4}$)"

            # Iterate through search results
            for index, result in enumerate(resp):
                output = "{}/{}: {}, title: {}, label: {}".format(\
                    index, len(resp), result["pid"], result["title"], result["label"])

                # Match "_yyyy", ask if to delete
                if re.search(regex, result["label"]):
                    match = re.search(regex, result["label"])
                    year = int(match.group(0)[1:])
                    if year > year_threadhold:
                        # remove item
                        if dry_run:
                            output += " - matched with year {} and can be removed from solr index - dry run!".format(year)
                        else:
                            # actually remove the record
                            solr.delete(queries=solr.Q(pid=result["pid"]))
                            solr.commit()
                            output += " - matched with year {} and is removed from solr index".format(year)
                        record = {"pid": result["pid"], "title": result["title"], "label": result["label"], "year": year}
                        summary.append(record)
                print output
            print "\n"

            # Print summary when there is one
            if len(summary) > 0:
                if dry_run:
                    print "Dry run summary:"
                else:
                    print "Index deletion summary:"

                for record in summary:
                    print record

        # When there is no matching result
        else:
            print "No matching condition found. Aborted."

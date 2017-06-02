from eulfedora.server import DigitalObject
import rdflib
from rdflib.namespace import RDF, Namespace
from eulfedora.models import  ReverseRelation
from eulfedora.server import Repository
from eulfedora.server import DigitalObject
from django.conf import settings
from pidservices.djangowrapper.shortcuts import DjangoPidmanRestClient
import datetime
from django.core.management.base import BaseCommand, CommandError

import os
os.environ['REQUESTS_CA_BUNDLE'] = os.path.join('/Users/yli60', 'ca-bundle.crt')
REPOMGMT = Namespace(rdflib.URIRef('info:fedora/fedora-system:def/relations-external#'))

class ScannedVolume(DigitalObject):
    """
    Subclass to collect all the pids realated to an ETD. We use the `ReverseRelation` so we can be
    confident that the related pids are aware they are related to an ETD that needs to be deleated.
    The `Related` subclass ensures that the pid is only realated to one ETD.
    """
    pageDObjs = ReverseRelation(relation=REPOMGMT.isConstituentOf, type=DigitalObject, multiple=True)

    def related(self):
        return {
            self.pid:{
                'Pages': [v.pid for v in self.pageDObjs] if self.pageDObjs is not None else []
            }
        }

    def get_pages(self):
        pages = []
        [(pages.append(p.pid)) for p in self.pageDObjs]
        return pages

class Related(DigitalObject):
    """
    Sublass used to double check that the related pid is only associated with one ETD.
    """
    is_constituent_of = ReverseRelation(relation=REPOMGMT.hasAuthorInfo, type=DigitalObject, multiple=True)
    def cont_of_count(self):
        return len(self.is_constituent_of) <= 1
    def check(self):
        return True if self.con_of_count else False


class Command(BaseCommand):

    def handle(self, *pids, **options):
        # testPid
        # settings.PIDMAN_HOST = 'https://testpid.library.emory.edu/'  # the web root where we'll ask for pids
        # settings.PIDMAN_USER = ''
        # settings.PIDMAN_PASSWORD = ''
        # settings.PIDMAN_DOMAIN = 'https://testpid.library.emory.edu/domains/18/'  # default domain (e.g. when minting pids)

        # prodPid
        # PIDMAN_HOST = 'https://pidqas.library.emory.edu/'

        # get a pidman client
        client = DjangoPidmanRestClient()

        # testFedora
        repo = Repository(settings.FEDORA_ROOT, username=settings.FEDORA_MANAGEMENT_USER, password=settings.FEDORA_MANAGEMENT_PASSWORD)

        # prodFedora
        #repo = Repository('https://fedora.library.emory.edu:8443/fedora/', username='ppppppp', password='pppppp')

        # constants
        REPOMGMT = Namespace(rdflib.URIRef('info:fedora/fedora-system:def/relations-external#'))
        vol_list = repo.get_objects_with_cmodel('info:fedora/emory-control:ScannedVolume-1.0')

        print "Found " + str(len(vol_list)) + " books."

        # Get a file logger
        filename = "ecds/" + str(datetime.datetime.now().strftime("%I-%M-%S %B-%d-%Y")) + ".csv"
        f = open(filename, 'w+')

        # report all books
        f.write("Found " + str(len(vol_list)) + " books.")
        f.write("\n")

        # report titles
        f.write("TYPE,")
        f.write("PID,")
        f.write("NOID,")
        f.write("O_URI,")
        f.write("N_URI,")
        f.write("PAGE,")
        f.write("POST_URI,")
        # f.write("POST_PDF_URI,")
        f.write("\n")



        # go over all books
        for vol in vol_list:
            volDobj = repo.get_object(vol.pid.rstrip(), type=ScannedVolume)

            # get attributes
            pid = volDobj.pid
            noid = pid.split(":")[1]
            try:
                pidmanObj = client.get_pid("ark", noid)
            except Exception as e:
                f.write(str(pid))
                f.write("\n")
                f.write(str(e))
                continue # continue to the next item
            oriTargetUri = pidmanObj["targets"][0]["target_uri"]
            newTargetUri = oriTargetUri

            # if it has emory%3A
            if newTargetUri.find("emory%3A") != -1:
                newTargetUri = newTargetUri.replace("emory%3A", "emory:")

            # if it has readux%3A
            if newTargetUri.find("readux%3A") != -1:
                newTargetUri = newTargetUri.replace("readux%3A", "emory:")

            # if it has readux:
            if newTargetUri.find("readux:") != -1:
                newTargetUri = newTargetUri.replace("readux:", "emory:")

            # if it has webprd001.library.emory.edu/readux
            if newTargetUri.find("webprd001.library.emory.edu/readux") != -1:
                newTargetUri = newTargetUri.replace("webprd001.library.emory.edu/readux", "testreadux.ecds.emory.edu")

            # if it has webprd001.library.emory.edu
            if newTargetUri.find("webprd001.library.emory.edu/") != -1:
                newTargetUri = newTargetUri.replace("webprd001.library.emory.edu/", "testreadux.ecds.emory.edu/")

            # if it has /readux/
            if newTargetUri.find("/readux/") != -1:
                newTargetUri = newTargetUri.replace("/readux/", "/")


            newTargetUri = unicode(newTargetUri)

            # log attributes
            f.write("BOOK" + ", ")
            f.write(str(pid) + ", ")
            f.write(str(noid) + ", ")
            f.write(str(oriTargetUri) + ", ")
            f.write(str(newTargetUri) + ", ")
            f.write(str(len(volDobj.pageDObjs)) + ", ")
            f.write("\n")

            # report attributes
            print("BOOK - " + str(pid) + " - " + str(len(volDobj.pageDObjs)) + " pages")

            #TODO update target
            # if newTargetUri != oriTargetUri:
            #     response = client.update_target(type="ark", noid=noid, target_uri=newTargetUri)
            #     updated_target_uri = response["target_uri"]
            #     response = client.update_target(type="ark", noid=noid, target_uri=newTargetUri, qualifier="PDF")
            #     updated_pdf_target_uri = response["target_uri"]
            #     f.write(str(updated_target_uri) + ", ")
            #     f.write(str(updated_pdf_target_uri) + ", ")

            # update pages
            page_count = 0
            for p in volDobj.get_pages():
                page_count = page_count + 1

                # Get all relevant attributes
                pid = p
                noid = pid.split(":")[1]
                try:
                    pidmanObj = client.get_pid("ark", noid)
                except Exception as e:
                    f.write(str(pid))
                    f.write("\n")
                    f.write(str(e))
                    continue # continue to the next item
                oriTargetUri = pidmanObj["targets"][0]["target_uri"]
                newTargetUri = unicode(oriTargetUri)

                # if it has readux%3A
                if newTargetUri.find("readux%3A%7B%25PID%25%7D") != -1:
                    newTargetUri = newTargetUri.replace("readux%3A%7B%25PID%25%7D", pid)

                # if it has readux:abc1234
                if newTargetUri.find("readux:") != -1:
                    newTargetUri = newTargetUri.replace("readux:", "emory:")

                # if it has readux%3A
                if newTargetUri.find("readux%3A") != -1:
                    newTargetUri = newTargetUri.replace("readux%3A", "emory:")

                # if it has /readux/
                if newTargetUri.find("/readux/") != -1:
                    newTargetUri = newTargetUri.replace("/readux/", "/")

                # if it has webprd001.library.
                if newTargetUri.find("webprd001.library.emory.") != -1:
                    newTargetUri = newTargetUri.replace("webprd001.library.emory.", "testreadux.ecds.emory.")

                newTargetUri = unicode(newTargetUri)

                # Log attributes
                f.write("page"+ ", ")
                f.write(str(pid) + ", ")
                f.write(str(noid) + ", ")
                f.write(str(oriTargetUri) + ", ")
                f.write(str(newTargetUri) + ", ")
                f.write(str(page_count) + ", ")

                try:
                    print(str(page_count) + "/" + str(len(volDobj.pageDObjs)) + " - " + str(noid) + " - page update")
                    #TODO update target
                    # if newTargetUri != oriTargetUri:
                    #     response = client.update_target(type="ark", noid=noid, target_uri=newTargetUri)
                    #     updated_target_uri = response["target_uri"]
                    #     response = client.update_target(type="ark", noid=noid, target_uri=newTargetUri, qualifier="PDF")
                    #     updated_pdf_target_uri = response["target_uri"]
                    #     f.write(str(noid) + " - page success" + ", ")
                    #     f.write(str(noid) + " - page pdf success" + ", ")
                except:
                    print(str(page_count) + "/" + str(len(volDobj.pageDObjs)) + " - " + str(noid) + " - page fail")
                    f.write(str(noid) + " - page fail" + ", ")

                f.write("\n")

            f.write("\n")

        f.close()

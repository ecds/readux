function annotatorMeltdownZotero(options) {
    var _t = annotator.util.gettext;
    var options = options || {};
    var zotero, zotero_initialized = false;

    var modal_template = $([
        '<div id="zotero-modal" class="modal" tabindex="-1" role="dialog">',
        '<div class="modal-dialog"><div class="modal-content">',
        // '<div class="modal-header"><button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span></button>',
            '<div class="modal-body">',
                '<label for="zotero-lookup">Z</label>',
                '<input id="zotero-lookup"/>',
                '<span class="in-progress" style="display:none"><i class="fa fa-2x fa-spinner fa-spin"></i></span>',
        '</div></div>',
        '</div></div>'].join('\n'));

    function customize_meltdown() {
        // add a Zotero citation action to default meltdown controls
        var controls = $.meltdown.defaults.controls,
            fs_index = controls.indexOf('fullscreen');
        // insert zotero before fullscreen
        controls.splice(fs_index, 0, 'zotero');
        // configure display and functionality for zotero
        $.meltdown.controlDefs.zotero = {
            label: "Z",
            altText: "Insert Zotero citation",  // based on examples in meltdown code
            click: function(meltdown /*, def, control, execAction */) {
                zotero_lookup(meltdown);
            }
        };
    }

    function has_citations(text) {
        return text !== undefined && text.indexOf('### Works Cited') != '-1';
    }
/* sample markdown annotation syntax ?
[#Beyer2013]: http://dx.doi.org/ 10.1093/annonc/mds579 "Maintaining success, reducing treatment burden,
focusing on survivorship: highlights from the third European consensus conference on diagnosis and
treatment of germ-cell cancer."
*/
    function zotero_lookup(meltdown) {
        if (! zotero_initialized) {
            $('#zotero-modal').on('shown.bs.modal', function () {
                // focus on the autocomplete lookup input, and select
                // any existing input from previous lookups for easy re-entry
                $('#zotero-lookup').focus().select();

                // make sure zotero modal shows up over the meltdown window
                $('#zotero-modal').zIndex(parseInt($('.meltdown_wrap').zIndex()) + 1);

                // for simplicity, hide the editor while the zotero lookup is active
                $('.annotator-editor').hide();

                // FIXME: would be nicer not to do this when meltdown is
                // fullscreen, which is easy to check;
                // however, zotero-modal does not show up *over* the fullscreen
                // meltdown window (and it does not seem to be a z-index issue)
            });
            $('#zotero-modal').on('hidden.bs.modal', function () {
                // restore editor visibility
                $('.annotator-editor').show();
            });

            $( "#zotero-lookup" ).autocomplete({
                autoFocus: true,
                source: function( request, response ) {
                    $('#zotero-modal .in-progress').show();
                    // execute a zotero autocomplete search on the user term
                    // for use with the autocomplete response method
                    zotero.autocomplete_search(request.term, function(data) {
                        $('#zotero-modal .in-progress').hide();
                        response(data);
                    });
                },
                open: function(event, ui) {
                    /* annotator purposely sets the editor at a higher z-index
                    than anything else on the page; make sure the autocomplete
                    menu is still higher so it isn't obscured by annotator buttons */
                    $('.ui-autocomplete').zIndex($(event.target).zIndex() + 1);
                },
                select: function(event, ui) {
                    // on select, put the citation id into the annotation text
                    // and hide the modal
                    if (meltdown) {  // requires access to meltdown editor
                        // get the zotero citation as html and add to the end of the text
                        // format json, include bib


                        zotero.get_item(ui.item.id, 'json', 'bib,data', function(data) {
                            // construct in-text citation with internal link;
                            // using chicago style for now (zotero default)
                            var text_label;
                            // zotero handles one, two, multiple authors for us
                            if (data.meta.creatorSummary) {
                                text_label = data.meta.creatorSummary;
                            // otherwise, cite in text by title (e.g. website)
                            } else if (data.data.shortTitle) {
                                text_label = data.data.shortTitle;
                            } else {
                                text_label = data.data.title;
                            }
                            // include first 4 letters (year) of date, if available
                            if (data.meta.parsedDate) {
                                text_label += ' ' + data.meta.parsedDate.substring(0, 4);
                            }

                            // construct parenthetical markdown internal link;
                            // using zotero item key as identifier
                            var text_citation = '([' + text_label + '](./#' + data.key + '))';
                            // insert in-text citation where the cursor is
                            meltdown.editor.replaceSelectedText(text_citation,
                                "select");

                            // parse the html citation from the zotero result
                            // and pull out just the entry
                            var citation = $($.parseXML(data.bib)).find("[class=csl-entry]");

                            var textarea = $(meltdown.editor.context);
                            var ed_content = textarea.val();

                            // add a new citations section if not already present
                            if (! has_citations(ed_content)) {
                                ed_content += '\n\n---\n### Works Cited\n';
                            }
                            // add the citation at the end of the annotation content
                            // using formatted citation from Zotero, but adding a named
                            // anchor for linking to in-text citation
                            ed_content += '\n* <a name="' + data.key + '"></a>' + citation.html();
                            textarea.val(ed_content);

                            console.log('editor val = ' + meltdown.editor.val());
                        });

                    }
                    // close the modal
                    $('#zotero-modal').modal('hide');
                },
            })
            .autocomplete( "instance" )._renderItem = function( ul, item ) {
                // customized display for zotero item
                return $( "<li>" )
                    .append("<a id='" + item.id + "'>" + item.title + "</a>")
                    .append('<p>' + item.description + '</p>')
                    .appendTo( ul );
            };
        }

        // show the modal
        $('#zotero-modal').modal();
    }


    // convert zotero citation references into full markdown citations
    function update_citations(annotation) {
        var name_re = new RegExp('a name="([^"]+)"', 'gm');
        var matches = [], found;

        console.log('update citations, annotation text is ' + annotation.text);

        // if annotation includes citations, scan for zotero ids
        // and attach additional data to the annotation
        if (has_citations(annotation.text)) {
            // list of promises, one for each api request to be done
            var promises = [];

            // Look for name anchors like those created by adding
            // citations in order to find all possible citation ids
            while (found = name_re.exec(annotation.text)) {
                matches.push(found[1]);   // 0 is full match, 1 is first group
            }

            // retrieve & store the tei citation information as extra data
            // on the annotation

            // clear out any stored citations to ensure content and tei
            // citations stay in sync
            annotation.citations = [];
            for(var i = 0; i < matches.length; i++) {
                // get tei record for full metadata & easy export
                // NOTE: tei record includes zotero item id, so not
                // fetching or storing id separately

                promises.push(new Promise(function(resolve, reject) {
                    zotero.get_item(matches[i], 'tei', '', function(data) {
                        console.log('fetched tei');
                        // zotero returns the citation wrapped in a listBibl
                        // element that we don't need; just extract the bibl itself
                        var tei_data = $($.parseXML(data)).find("biblStruct");
                        var tei_bibl = tei_data.get(0).outerHTML;
                        // don't duplicate an entry (could happen due to delayed processing)
                        if (annotation.citations.indexOf(tei_bibl) == -1) {
                            annotation.citations.push(tei_bibl);
                        }

                        console.log('annotation citations = ');
                        console.log(annotation.citations);

                        // resolve the promise after the api request is processed
                        resolve();
                    });

                }));
            }  // for loop on matches


            // return a promise that will resolve when all promises resolve,
            // so annotator will wait to save the annotation until
            // all citations are processed and data is added
            return Promise.all(promises);

          } // has citations
        }; // update citations


    return {

        start: function (app) {
            // any startup config / warnings needed?

            // check for meltdown
            if (!jQuery.meltdown || typeof jQuery.meltdown !== 'object') {
                console.warn(_t("To use the annotator-meltdown-zotero Editor " +
                    "extension, you must include meltdown in the page."));
                return;
            }

            // also check for annotator-meltdown?  zotero client? jquery.rest ?

            customize_meltdown();

            // if required options are not present, disable with a message
            if (!(options.user_id && options.token)) {
                console.log('disabling');
                // todo: actually disable somehow, with message to user

            } else {

                // dynamically add modal for zotero autocomplete into the document
                // using bootstrap modal markup
                // zotero word CWYW modal has a red border with zotero z label for input bot
                $('body').append(modal_template);

                // init zotero rest api client;
                zotero = new ZoteroClient(options);
            }

            // for testing: uncomment to launch zotero lookup on page load
            // zotero_lookup();

        },

        // TODO: maybe add a custom event to annotator-meltdown
        // that can fire off whenever the editor is closed,
        // so the annotation content can be updated then?

        beforeAnnotationCreated: function (annotation) {
            // FIXME: this event seems to fire before annotation text
            // is populated, when editor is displayed - not
            // when editor is closed
            return update_citations(annotation);
        },

        beforeAnnotationUpdated: function (annotation) {
            // FIXME: sometimes seems to be called when annotation is
            // loaded for edit, not when the editor is closed
            return update_citations(annotation);
        }
    };
};



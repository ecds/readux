/* Meltdown viewer and editor integration for annotatorjs.
   Based in part on annotator.ui.markdown.

   Include annotator.meltdown.css to adjust for annotator/meltdown
   style interactions.
*/

var _t = annotator.util.gettext;

var annotatormeltdown = {

    /**
     * Replacement viewer render method.
     * Returns annotation text content parsed as Markdown.
     */
    render: function (annotation) {
        if (annotation.text) {
            return Markdown(annotation.text);
        } else {
            return "<i>" + _t('No comment') + "</i>";
        }
    },

    /**
     * function:: viewerExtension(viewer)
     *
     * An extension for the :class:`~annotator.ui.viewer.Viewer`. Allows the
     * viewer to interpret annotation text as `Markdown`_ and uses the
     * `js-markdown-extra`_ library if present in the page to render annotations
     * with Markdown text as HTML.
     *
     * .. _Markdown: https://daringfireball.net/projects/markdown/
     * .. _js-markdown-extra: https://github.com/tanakahisateru/js-markdown-extra
     *
     * **Usage**::
     *
     *     app.include(annotator.ui.main, {
     *         viewerExtensions: [annotatormeltdown.viewerExtension]
     *     });
     */
    viewerExtension: function viewerExtension(viewer) {
        if (!window.Markdown || typeof window.Markdown !== 'function') {
            console.warn(_t("To use the Meltdown viewer extension, you must " +
                "include markdown in the page."));
            return;
        }
        // only set the renderer when Markdown is available
        viewer.setRenderer(annotatormeltdown.render);
    },


    // Editor textarea keyboard shortcuts.
    // Revise default annotator shortcut to map shift+enter to save
    // instead of just enter.
    textarea_keydown: function (event) {
        if (event.which === 27) {
            // "Escape" key => abort.
            this.cancel();
        } else if (event.which === 13 && event.shiftKey) {
            // If "return" was pressed *with*the shift key, we're done.
            this.submit();
        }
    },

    // Extend Editor show method to initialize meltdown and set minimum
    // width the first time the editor window is shown.
    show: function(position) {
        // use unextended method to handle normal show functionality
        this._pre_meltdown_show(position);
        // enable meltdown on the textarea and set a min-width
        if (! this.meltdown_initialized) {
            $(this.element).find("textarea").meltdown({
                previewCollapses: false,
                openPreview: true
            });
            if (this.meltdown_options.min_width) {
                this.element.find('.annotator-widget')
                    .css('min-width', this.meltdown_options.min_width);
            }
            this.meltdown_initialized = true;
        } else {
            // make sure preview area is updated for current text
            $(this.element).find("textarea").meltdown("update");
        }
        // always ensure textarea has focus for immediate input
        $(this.element).find("textarea").focus();
    },

    // NOTE: extending checkOrientation here to work around a bug
    // where control buttons (save/cancel) are added after every ul
    // in the widget and show up multiple times.
    // Pull request for this fix: https://github.com/openannotation/annotator/pull/533
    // Remove this workaround once the fix is in a released version
    // of annotator.
    checkOrientation: function () {
        annotator.ui.widget.Widget.prototype.checkOrientation.call(this);

        var list = this.element.find('ul').first(),
            controls = this.element.find('.annotator-controls');

        if (this.element.hasClass(this.classes.invert.y)) {
            controls.insertBefore(list);
        } else if (controls.is(':first-child')) {
            controls.insertAfter(list);
        }

        return this;
    },


    /**
     * function:: getEditorExtension(options)
     *
     * Build and return an extension for :class:`~annotator.ui.editor.Editor`.
     * Converts the editor textarea to a `Meltdown`_ input, with preview
     * panel and toolbar
     *
     * .. _Meltdown: https://github.com/iphands/Meltdown
     *
     * **Usage**::
     *
     *     app.include(annotator.ui.main, {
     *         editorExtensions: [annotatormeltdown.getEditorExtension()]
     *     });
     *
     * You can optionally specify a minimum editor window width (by default,
     * minimum width will be set to 375px):
     *
     *     app.include(annotator.ui.main, {
     *         editorExtensions: [annotatormeltdown.getEditorExtension({min_width: '500px'})]
     *     });
     */
    getEditorExtension: function getEditorExtension(options) {

        var meltdown_opts = {
            min_width: '375px'  // default minimum width
        };
        $.extend(meltdown_opts, options);
        return function editorExtension(editor) {
            // Make sure meltdown is available before configuring anything
            if (!jQuery.meltdown || typeof jQuery.meltdown !== 'object') {
                console.warn(_t("To use the Meltdown editor extension, you must " +
                    "include meltdown in the page."));
                return;
            }
            // override editor methods and add options
            editor._onTextareaKeydown = annotatormeltdown.textarea_keydown;
            editor._pre_meltdown_show = editor.show; // preserve unextended show method
            editor.show = annotatormeltdown.show;
            editor.checkOrientation = annotatormeltdown.checkOrientation;
            // track meltdown initialization since it only needs to be done once
            editor.meltdown_initialized = false;
            editor.meltdown_options = meltdown_opts;
        };
    },
};

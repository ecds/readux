/* annotatormeltdown  - meltdown integration for annotator */
/* based on annotator.ui.markdown */

var _t = annotator.util.gettext;

var annotatormeltdown = {

    render: function (annotation) {
        if (annotation.text) {
            return Markdown(annotation.text);
        } else {
            // return "<i>No comment)</i>";
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
     *         viewerExtensions: [readuxannotator.meltdown.viewerExtension]
     *     });
     */
    viewerExtension: function viewerExtension(viewer) {
        if (!window.Markdown || typeof window.Markdown !== 'function') {
            console.warn(_t("To use the Meltdown plugin, you must " +
                "include markdown into the page first."));
            // console.warn("To use the Meltdown plugin, you must " +
                // "include js-markdown-extra in the page first.");
            return;
        }
        // only set the renderer when Markdown is available
        viewer.setRenderer(annotatormeltdown.render);
    },


    // map shift+enter to save instead of just enter
    textarea_keydown: function (event) {
        if (event.which === 27) {
            // "Escape" key => abort.
            this.cancel();
        } else if (event.which === 13 && event.shiftKey) {
            // If "return" was pressed *with*the shift key, we're done.
            this.submit();
        }
    },

    editorExtension: function editorExtension(editor) {
        console.log('editor extension');
        console.log(editor);
        // this doesn't seem to work (template used already at this point?)
        //annotator.ui.editor.Editor.template = readuxannotator.meltdown.editor_template;

        editor._onTextareaKeydown = annotatormeltdown.textarea_keydown;
    }
};

/*
TESTING
... extend Editor and create a module instead of using an Editor extension?
(not yet functional)

var MeltdownEditor = annotator.ui.editor.Editor.extend({
    options: {
        defaultFields: true,
    }
});

// HTML template for this.element.
MeltdownEditor.template = [
    '<div class="annotator-outer annotator-editor annotator-hide">',
    '  <form class="annotator-widget">',
    '  <p>Meltdown TEST</p>',
    '    <ul class="annotator-listing"></ul>',
    '    <div class="annotator-controls">',
    '     <a href="#cancel" class="annotator-cancel">' + _t('Cancel') + '</a>',
    '      <a href="#save"',
    '         class="annotator-save annotator-focus">' + _t('Save') + '</a>',
    '    </div>',
    '  </form>',
    '</div>'
].join('\n');


var meltdown_editor = function (options) {
    var widget = new MeltdownEditor(options);

    return {
        destroy: function () { widget.destroy(); },
        beforeAnnotationCreated: function (annotation) {
            return widget.load(annotation);
        },
        beforeAnnotationUpdated: function (annotation) {
            return widget.load(annotation);
        }
    };
}; */
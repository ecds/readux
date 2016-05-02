var suppress_permissions = {

    show: function(position) {
        // do normal show functionality
        this._pre_suppress_permissions_show(position);
        this.element.find('.annotator-checkbox').filter(':contains("Allow anyone to ")').hide();
    },

    editorExtension: function editorExtension(editor) {
        // preserve existing show method
        editor._pre_suppress_permissions_show = editor.show;
        // override with local show method
        editor.show = suppress_permissions.show;

    },
};

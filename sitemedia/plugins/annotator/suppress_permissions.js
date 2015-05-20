var suppress_permissions = {

    show: function(position) {
        // do normal show functionality
        this._pre_suppress_permissions_show(position);
        console.log(this.element.find('.annotator-checkbox'));
        this.element.find('.annotator-checkbox').filter(':contains("Allow anyone to ")').hide();

    },

    editorExtension: function editorExtension(editor) {
        console.log("suppress_permissions");
        // preserve existing show method
        editor._pre_suppress_permissions_show = editor.show;
        // override with local show method
        editor.show = suppress_permissions.show;

    },
};

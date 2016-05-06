/* convenience funtions */

// capitalize the first letter of a string and return it
String.prototype.capitalize = function() {
    return this.charAt(0).toUpperCase() + this.slice(1);
}

/**

Annotator module for group permissions.

- editor extension adds a multiple select input for each permission
  (read, update, delete).  Groups that user is a member of or
  has access to share with should be passed in as editor options, e.g.:

    editorExtensions: [
      annotation_permissions.getEditorExtension({
        groups: {
          "group:1": "class team 1",
          "group:5": "my annotation friends"
        }
      }),
  ]

- currently required to also be included as a module in order to workaround
  a limitation with the permissions handling in annotator.ui.main:

    .include(annotation_permissions.getModule);

- input fields are currently grouped and styled using bootstrap css

- Extends default SimpleIdentityPolicy to allow checking for group
  and superuser permissions. Those should be set similar to the way that
  the default identity is:

      app.ident.identity = "username";
      app.ident.groups = ['mygroup1', 'group2'];
      app.ident.is_superuser = false;

*/


/* based on annotator SimpleIdentityPolicy */

var IdentityPolicy;

IdentityPolicy = function IdentityPolicy() {
    this.identity = null;
    this.groups = [];
    this.is_superuser = false;
};

IdentityPolicy.prototype.who = function () {
    return this.identity;
};

/* extend built-in authz policy with a method to check superuser and groups */
annotator.authz.AclAuthzPolicy.prototype.extended_permits = function (action, context, identity) {
    // as soon as we get a permitted response; otherwise, keep checking
    if (identity.is_superuser) { return true; }
    // username based check
    if (annotator.authz.AclAuthzPolicy.prototype.permits(action, context, identity.identity)) {
        return true;
    }
    // check each group id in turn
    for (var i = 0; i < identity.groups.length; i++) {
         if (annotator.authz.AclAuthzPolicy.prototype.permits(action, context, identity.groups[i])) {
            return true;
        }
    }
    return false;
}

var annotation_permissions = {
    options: {},
    permissions: ['read', 'update', 'delete'],
    getId: function(mode) {
        return 'annotator-permissions-' + mode;
    },
    getLabel: function(mode) {
        return $('<label>' + mode.capitalize() + '</label>')
            .attr('for', annotation_permissions.getId(mode));
    },

    getEditorExtension: function getEditorExtension(options) {
        // customize the editor to add permission editing

        annotation_permissions.options = options;

        return function editorExtension(editor) {
            // The input element added to the Annotator.Editor wrapped in jQuery.
            // Cached to save having to recreate it everytime the editor is displayed.
            var field, input;

            if ($.isEmptyObject(options.groups)) {
                console.warn('No groups are configured, not enabling permissions');
                return;
            }


            function loadPermissions(field, annotation) {
                // load permissions from the annotation object
                // to preselect groups that already have access
                var id, input;
                if (annotation.permissions)  {
                    for (var mode in annotation.permissions) {
                        id = annotation_permissions.getId(mode);
                        input = $(field).find('[id=' + id + ']');
                        // set input selection using array of group ids
                        input.val(annotation.permissions[mode]);
                    }
                }
            }

            function setPermissions(field, annotation) {
                // set annotation permissions based on selected
                // values on the edit form

                // NOTE: don't add any permissions data if nothing is selected
                var perms = $.extend({}, annotation.permissions),
                    item_index;
                // fixme: merge isn't right; need to make sure any *selected*
                // groups are present, and deselected groups are removed
                // for each permission mode, update who should have access
                $.each(annotation_permissions.permissions, function(index, mode) {
                    // iterate through each option and check if it is selected or not
                    $(field).find('[id=' + annotation_permissions.getId(mode) + ']')
                        .find('option').each(function(idx, opt){
                            if (! (mode in perms)) {
                                // make sure list exists so items can be added
                                perms[mode] = [];
                            }
                            item_index = perms[mode].indexOf(opt.value);

                            // if it is selected, make sure it is in the list
                            if (opt.selected) {
                                if (item_index === -1) {
                                    perms[mode].push(opt.value);
                                }
                            } else {
                                // if not selected, remove if previously listed
                                if (item_index > -1) {
                                    perms[mode].splice(item_index, 1);
                                }
                            }
                        });
                });

                // NOTE: currently, any permissions set here are overwritten
                // in a ui.main submit callback; as a workaround, store them
                // in a special field do be copied in place after that.
                if (perms.read || perms.update || perms.delete) {
                    annotation.rdx_permissions = perms;
                }
            }

            // use the editor add field method to create the initial
            // input and set hooks for load and submit methods
            var mode = annotation_permissions.permissions[0];
            var input_id = annotation_permissions.getId(mode);
            field = editor.addField({
                id: input_id,
                label: _t('permissions') + '\u2026',
                load: loadPermissions,
                submit: setPermissions,
                type: 'select',

            });
            var $field = $(field),
                $heading = $('<h3 class="annotation-permissions">Permissions</h3>'),
                $content_div = $('<div class="permission-contents" style="display:none"/>'),
                $div = $('<div class="form-group col-md-3"/>');

            // add a label for this section
            $field.prepend($heading);
            $heading.on('click', function() { $content_div.toggle(750); });
            // add a class for styling/identification purposes
            $field.addClass('permission row');
            $field.append($content_div);
            $content_div.append($('<p>Allow annotation group members access to this annotation.</p>'));

            // find the initial input and add a label
            input = $(field).find(':input');
            input.addClass('form-control');
            $content_div.append($div);
            input.detach().appendTo($div)
            annotation_permissions.getLabel(mode).insertBefore(input);

            // toggle, so perms are hidden by default

            // configure input to allow multiple selection
            input.attr('multiple', 'multiple')
            // add an option for each group passed in
            for (var group in options.groups) {
                input.append($("<option></option>")
                     .attr("value", group).text(options.groups[group]));
            }

            // copy the input and add labels for each other permission mode
            $.each(annotation_permissions.permissions, function(index, perm) {
                if (index == 0) { return; }  // skip first perm, already done

                // create a new form-group div
                $div = $('<div class="form-group col-md-3"/>');
                // generate and append a new label
                $div.append(annotation_permissions.getLabel(perm));
                // copy the first input, update the id, and append
                var copy = input.clone();
                copy.attr("id", annotation_permissions.getId(perm));
                $div.append(copy);
                $content_div.append($div);
            });
        }
    },

    _app: null,

    fix_permissions: function(annotation) {

        if ('rdx_permissions' in annotation) {
            // copy local perms over permissions, and delete local permissions
            annotation.permissions = annotation.rdx_permissions;
            delete annotation.rdx_permissions;

            // NOTE: may need to explicitly include the annotation author
            // in all roles, since annotator seems to behave somewhat
            // differently when permissions are set

            // workaround issue in main.ui:
            // if permissions are set, annotator adds the *current* anntotaor
            // identify, rather than the annotation author.
            // If that's present here, update so the author is listed.
            var ident = annotation_permissions._app.registry.getUtility('identityPolicy');
            if (annotation.permissions.read[0] == ident.who() &&
                ident.who() != annotation.user) {
                annotation.permissions.read[0] = annotation.user;
            }
            if (annotation.permissions.update[0] == ident.who() &&
                ident.who() != annotation.user) {
                annotation.permissions.update[0] = annotation.user;
            }

            // re-save the annotation after making changes
            annotation_permissions._app.registry.getUtility('storage').update(annotation);
            // update the display to re-render changes (marginalia specific)
            annotation_permissions.renderExtension(annotation,
                $('.marginalia-item[data-annotation-id=' + annotation.id + ']'));
        }

        return true;
    },

    identity: new IdentityPolicy(),

    getModule: function() {
        return {
            // name, for identification in list of annotator modules
            name: 'annotation-permissions',

            // configuration based on SimpleIdentityPolicy
            configure: function (registry) {
                registry.registerUtility(annotation_permissions.identity, 'identityPolicy');
            },
            beforeAnnotationCreated: function (annotation) {
                annotation.user = annotation_permissions.identity.who();
            },

            start: function (app) {
                // store a reference to the app, in order to retrieve
                // storage and identity
                annotation_permissions._app = app;
            },

            // NOTE: beforeAnnotationCreated and beforeAnnotationUpdated
            // seem like they should be the right hooks to use,
            // but they fire before the editor is loaded and
            // these updates need to happen after the editor is submitted.

            annotationCreated: function (annotation) {
                annotation_permissions.fix_permissions(annotation);
            },

            annotationUpdated: function(annotation) {
                annotation_permissions.fix_permissions(annotation);
            }
        };
    },

    renderExtension: function(annotation, item) {
        item.find('.annotation-permissions').remove();
        // nothing to do if no permissions are set
        if ($.isEmptyObject(annotation.permissions)) {
            // return item unchanged
            return item;
        }
        // get a list of people/groups other than current user with
        // permission on this annotation
        var shared_with = [];
        // combine lists from all permissions
        $.each(annotation.permissions, function(mode, values) {
            $.each(values, function(i, val) {
                // if not annotation author and not already present, add to list
                if (val != annotation.user && shared_with.indexOf(val) === -1) {
                    shared_with.push(val);
                }
            });
        });

        // if there is a list, add an icon
        if (shared_with.length) {
            // convert group identifiers into display names
            var group_names = [];
            $.each(shared_with, function(i, group_id) {
                group_names.push(annotation_permissions.options.groups[group_id]);
            });

            var perms_icon = $('<span class="annotation-permissions text-info pull-right"/>');
            perms_icon.attr('title', 'Shared with ' + group_names);
            perms_icon.append($('<i class="fa fa-users" aria-hidden="true"></i>'));
            item.find('.annotation-footer').append(perms_icon);
        }
        return item;
    },

};

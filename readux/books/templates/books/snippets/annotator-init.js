{% comment %}
Initialize annotator for use in page annotation OR
for searching annotations without full annotation.
Requires mode = full for full annotatoin functionality; expects
a volume_uri for loading annotations and filtering search.
{% endcomment %}

/* function to include page and volume urls in the annotation data */
{% if mode = 'full' %}
  var readuxUris = function () {
    return {
      beforeAnnotationCreated: function (ann) {
        ann.uri = '{{ page.absolute_url }}';
        ann.volume_uri = '{{ page.volume.absolute_url }}';
        {% if page.ark_uri %}
        ann.ark = '{{ page.ark_uri }}';
        {% endif %}
      }
    };
  };
{% endif %}
  var marginalia_opts = {
    show_author: true,
    viewer: annotatormeltdown.render,
    renderExtensions: [
        related_pages.renderExtension,
        annotation_permissions.renderExtension,
    ],
    toggle: {
      class: 'btn btn-green',
      show: function(){
        $(".carousel-control").fadeOut();
      },
      hide: function(){
        $(".carousel-control").fadeIn();
      }
    }
  };
  // configuring marginalia here so it can be referenced in annotator search
  var _marginalia = annotatorMarginalia(marginalia_opts);
  var app = new annotator.App()
    {% if mode = 'full' %}
      .include(annotator.ui.main, {
          element: document.querySelector('.content .inner'),
          {% comment %}/*  {# not using default viewer, so these don't matter, see marginalia #}
          viewerExtensions: [
              annotatormeltdown.viewerExtension,
              annotator.ui.tags.viewerExtension
          ],
          */{% endcomment %}
          editorExtensions: [
              annotatormeltdown.getEditorExtension({min_width: '500px', font_awesome: true}),
              related_pages.getEditorExtension({search_url: '{{ page.volume.get_absolute_url }}'}),
              _marginalia.editorExtension,  /* includes tags */
              annotation_permissions.getEditorExtension({
                groups: { {% for group in request.user.groups.all %}
                  "group:{{ group.id }}": "{{ group.name }}",
                {% endfor %} }
              }),
          ]
      })
      .include(readuxUris)
      .include(annotatorImageSelect, {
        element: $('.content .inner img'),
      })
      .include(annotatorSelectionId, {
        element: $('.content .inner'),
      })
      .include(annotatorMeltdownZotero, {
        user_id: '{{ zotero_userid }}', token: '{{ zotero_token}}',
        disabled_message: 'Please link your Zotero account to enable Zotero functionality',
      })
      {% endif %}
      .include(annotator.storage.http, {
          prefix: '{% url "annotation-api-prefix" %}',
          headers: {"X-CSRFToken": csrftoken}
      })
      .include(annotatorMarginalia, marginalia_opts)
      .include(annotatorSearch, {
        render: _marginalia.renderAnnotation,
        filter: {
          volume_uri: '{{ volume_uri }}'
        },
      })
      .include(annotation_permissions.getModule);

  app.start()
      .then(function () {
          {% if mode = 'full' %}
           app.annotations.load({uri: '{{ page.absolute_url }}'});
          {% endif %}
      });
  {# set user identity to allow for basic permission checking #}
  app.ident.identity = "{{ user.username }}";
  // set groups and superuser status to allow auth checking
  // (enforced at application level, only affects what is displayed)
  app.ident.groups = [{% for group in request.user.groups.all %}"group:{{ group.id }}", {% endfor %}];
  app.ident.is_superuser = {{ request.user.is_superuser|lower }};
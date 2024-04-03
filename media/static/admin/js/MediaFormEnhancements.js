'use strict';
{
  const $ = django.jQuery;

  const MediaFormEnhancements = {

    init: function() {
      MediaFormEnhancements.initFocusSearchOnOpenTaxonSelect();
      MediaFormEnhancements.initAutoUpdateTitleOnTaxonChange();
      MediaFormEnhancements.initSaveAndRestoreFieldsTemplate();
    },

    initFocusSearchOnOpenTaxonSelect() {
      // FIX: Set focus on search field when open select2 component.
      // This really is the default behavior but does no longer work
      // due to changes in how jQuery handles focus.
      $('[name=taxon]').on('select2:open', function(e) {
        const searchInput = $(this).data('select2').$dropdown.find(
          '.select2-search__field'
        );
        if (searchInput) {
          searchInput.get(0).focus();
        }
      });
    },

    initAutoUpdateTitleOnTaxonChange() {
      const taxonInput = $('[name=taxon]');
      const titleInput = $('[name=title]');

      let previouslySelectedName = '';

      taxonInput.on('change', function(e) {
        const selectedName = e.target.options[e.target.selectedIndex].textContent;

        if (titleInput.val() === previouslySelectedName) {
          titleInput.val(selectedName);
        }

        previouslySelectedName = selectedName;
      });
    },

    initSaveAndRestoreFieldsTemplate() {
      const STORAGE_KEY = 'media.template';

      const EXCLUDE_FIELDS = [
        'taxon',
        'file',
        'title',
      ];

      const form = $('#content-main > form');

      const fields = [
        ...form.find(`
          .form-row input[name],
          .form-row select[name],
          .form-row textarea[name]
        `)
      ].filter(
        element => EXCLUDE_FIELDS
          .includes(element.name) == false
      );

      const toolbarDOM = $(`
        <div class="media-template-toolbar">
          <button class="button" type="button" data-action="load">
            Load from template
          </button>
          <button class="button" type="button" data-action="save">
            Save as template
          </button>
        </div>
      `);

      toolbarDOM.on('click', '[data-action=load]', () => {
        const data = JSON.parse(
          localStorage.getItem(STORAGE_KEY) ?? '{}'
        );
        fields.forEach(element => {
          if (data[element.name] != null) {
            $(element).val(data[element.name]);
            $(element).trigger('change');
          }
        });
      });

      toolbarDOM.on('click', '[data-action=save]', () => {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(
          fields.filter(
            element => $(element).is(':checkbox, :radio')
              ? element.checked
              : true
          ).reduce(
            (data, element) => ({
              ...data,
              [element.name]: $(element).is(':checkbox, :radio')
                ? [...data[element.name] ?? [], $(element).val()]
                : $(element).val()
            }),
            {}
          )
        ));
      });

      toolbarDOM.insertBefore(form);
    },

  };

  $(MediaFormEnhancements.init);

}

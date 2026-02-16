'use strict';
{
  const $ = django.jQuery;

  const MediaFormEnhancements = {

    init: function() {
      MediaFormEnhancements.initFocusSearchOnOpenTaxonSelect();
      MediaFormEnhancements.initAutoUpdateTitleOnTaxonChange();
      MediaFormEnhancements.initAutoUpdateTitleOnZipUpload();
      MediaFormEnhancements.initAutoSelectTaxonFromZipFilename();
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

    initAutoUpdateTitleOnZipUpload() {
      const fileInput = $('[name=file]');
      const titleInput = $('[name=title]');

      if (fileInput.length && titleInput.length) {
        fileInput.on('change', function() {
          const file = this.files[0];
          
          if (file && file.name.toLowerCase().endsWith('.zip')) {
            // Extract filename without .zip extension
            const filename = file.name;
            const titleValue = filename.substring(0, filename.lastIndexOf('.'));
            
            // Set the title field
            titleInput.val(titleValue);
            
            // Trigger change event in case there are other listeners
            titleInput.trigger('change');
          }
        });
      }
    },

    initAutoSelectTaxonFromZipFilename() {
      const fileInput = $('[name=file]');
      const taxonSelect = $('[name=taxon]');

      if (!fileInput.length || !taxonSelect.length) {
        return;
      }

      fileInput.on('change', function() {
        const file = this.files[0];
        if (!file || !file.name.toLowerCase().endsWith('.zip')) {
          return;
        }

        // Extract taxon name from filename
        let name = file.name;
        name = name.replace(/\.zip$/i, '');           // Remove .zip
        name = name.replace(/_/g, ' ');               // Underscores to spaces
        name = name.replace(/\b(sp|spp|cf)\.?\b/gi, ''); // Remove sp/spp/cf
        name = name.replace(/\s+/g, ' ').trim();      // Clean whitespace

        if (!name) return;

        // Check if it's a Select2 autocomplete widget
        if (taxonSelect.data('select2')) {
          const autocompleteUrl = taxonSelect.data('ajax--url');
          if (autocompleteUrl) {
            $.ajax({
              url: autocompleteUrl,
              data: { term: name },
              dataType: 'json',
              success: function(data) {
                if (data.results && data.results.length > 0) {
                  // Find best match (exact, then first result)
                  const match = data.results.find(item =>
                    item.text.toLowerCase() === name.toLowerCase()
                  ) || data.results[0];

                  // Set the value in Select2
                  const option = new Option(match.text, match.id, true, true);
                  taxonSelect.append(option).trigger('change');
                }
              }
            });
          }
        } else {
          // Regular <select>: search through options
          const selectElement = taxonSelect[0];
          const options = selectElement.options;
          let bestMatch = null;
          const nameLower = name.toLowerCase();

          // Try exact match first (case-insensitive)
          for (let i = 0; i < options.length; i++) {
            if (options[i].text.toLowerCase() === nameLower) {
              bestMatch = options[i];
              break;
            }
          }

          // Then try starts-with
          if (!bestMatch) {
            for (let i = 0; i < options.length; i++) {
              if (options[i].text.toLowerCase().startsWith(nameLower)) {
                bestMatch = options[i];
                break;
              }
            }
          }

          // Then try if the search term starts with option text (for genus-level matches)
          if (!bestMatch) {
            for (let i = 0; i < options.length; i++) {
              if (nameLower.startsWith(options[i].text.toLowerCase())) {
                bestMatch = options[i];
                break;
              }
            }
          }

          if (bestMatch) {
            taxonSelect.val(bestMatch.value).trigger('change');
          }
        }
      });
    },

    initSaveAndRestoreFieldsTemplate() {
      const STORAGE_KEY = 'media.template';

      const EXCLUDE_FIELDS = [
        'taxon',
        'file',
        'title',
        'caption',
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

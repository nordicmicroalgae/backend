'use strict';
{
  const $ = django.jQuery;

  const MediaFormEnhancements = {

    init: function() {
      MediaFormEnhancements.initFocusSearchOnOpenTaxonSelect();
      MediaFormEnhancements.initAutoUpdateTitleOnTaxonChange();
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
    }
  };

  $(MediaFormEnhancements.init);

}

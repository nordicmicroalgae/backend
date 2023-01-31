'use strict';
{

  const MediaFormEnhancements = {

    init: function() {
      MediaFormEnhancements.initAutoUpdateTitleOnTaxonChange();
    },

    initAutoUpdateTitleOnTaxonChange() {
      const taxonInput = document.querySelector('[name=taxon]');
      const titleInput = document.querySelector('[name=title]');

      let previouslySelectedName = '';

      taxonInput.addEventListener('change', function(e) {
        const selectedName = e.target.options[e.target.selectedIndex].textContent;

        if (titleInput.value === previouslySelectedName) {
          titleInput.value = selectedName;
        }

        previouslySelectedName = selectedName;
      });
    }
  };

  window.addEventListener('load', MediaFormEnhancements.init);

}

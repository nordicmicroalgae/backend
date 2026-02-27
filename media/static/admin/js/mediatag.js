'use strict';
{
  const $ = django.jQuery;

  function getParentGalleries($select) {
    const parents = new Set();

    $select.find('option').each(function () {
      const val = $(this).val();
      const slashIndex = val.indexOf('/');

      if (slashIndex !== -1) {
        parents.add(val.substring(0, slashIndex));
      } else if (val) {
        parents.add(val);
      }
    });

    return Array.from(parents).sort();
  }

  function addSubgalleryHelper($select) {
    const parents = getParentGalleries($select);

    if (parents.length === 0) return;

    // Place the helper on the .form-row so it sits below the floated
    // label + widget div that Django admin uses in .aligned fieldsets.
    const $formRow = $select.closest('.form-row');
    if ($formRow.length === 0) return;
    if ($formRow.find('.subgallery-helper').length > 0) return;

    const parentOptions = parents
      .map(function (p) {
        const escaped = $('<span>').text(p).html();
        return '<option value="' + escaped + '">' + escaped + '</option>';
      })
      .join('');

    const $helper = $(
      '<div class="subgallery-helper">' +
        '<label>Add subgallery:</label>' +
        '<select class="subgallery-parent">' +
          parentOptions +
        '</select>' +
        '<span class="subgallery-separator">/</span>' +
        '<input type="text" class="subgallery-child" placeholder="subgallery name" />' +
        '<button type="button" class="subgallery-add button">Add</button>' +
      '</div>'
    );

    $formRow.append($helper);

    $helper.find('.subgallery-add').on('click', function () {
      var parent = $helper.find('.subgallery-parent').val();
      var child = $.trim($helper.find('.subgallery-child').val());

      if (!child) return;

      var fullValue = parent + '/' + child;

      // Add as a new <option> if it doesn't exist, then select it
      if ($select.find('option[value="' + CSS.escape(fullValue) + '"]').length === 0) {
        $select.append(
          $('<option>', { value: fullValue, text: fullValue, selected: true })
        );
      } else {
        $select.find('option[value="' + CSS.escape(fullValue) + '"]').prop('selected', true);
      }

      $select.trigger('change');
      $helper.find('.subgallery-child').val('');
    });

    // Allow pressing Enter in the text input
    $helper.find('.subgallery-child').on('keydown', function (e) {
      if (e.key === 'Enter') {
        e.preventDefault();
        $helper.find('.subgallery-add').trigger('click');
      }
    });
  }

  $(function () {
    $('.media-tag-widget').each(function () {
      var $el = $(this);
      $el.select2();

      // Add subgallery helper only for the galleries field
      if ($el.attr('name') === 'galleries') {
        addSubgalleryHelper($el);
      }
    });
  });
}

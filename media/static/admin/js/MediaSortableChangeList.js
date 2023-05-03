'use strict';
{
  const $ = django.jQuery;

  const DIRECTION_ASCENDING = Symbol('ascending');
  const DIRECTION_DESCENDING = Symbol('descending');

  class SortableChangeListConfig {
    constructor(config) {
      this.config = config;
    }

    get postURL() {
      return this.config.postURL;
    }

    get postDelay() {
      return this.config.postDelay ?? 0;
    }

    static fromDOMNode(node) {
      return new SortableChangeListConfig({
        postURL: $(node).data('post-url'),
        postDelay: $(node).data('post-delay')
      });
    }
  }

  class SortableChangeList {
    constructor(table, config) {
      this.table = $(table);
      this.config = config;
      this.timer = null;

      const firstRowPriority = this.getPriority(this.rows.first());
      const lastRowPriority = this.getPriority(this.rows.last());

      if (firstRowPriority < lastRowPriority) {
        this.direction = DIRECTION_ASCENDING;
      } else {
        this.direction = DIRECTION_DESCENDING;
      }

      this.table.on('click', 'button[data-action]', this.dispatch);
    }

    get rows() {
      return this.table.find('tbody > tr');
    }

    get list() {
      const list = Array.from(
        this.rows.find('[data-pk]').map(
          (_index, node) => $(node).data('pk')
        )
      );
      return (
        this.direction === DIRECTION_ASCENDING
          ? list
          : list.reverse()
      );
    }

    get buttons() {
      return this.rows.find('button[data-action]');
    }

    get csrfToken() {
      return $('[name=csrfmiddlewaretoken]').val();
    }

    getPriority = node => {
      return $(node).find('[data-priority]').data('priority');
    }

    dispatch = ev => {
      const actions = {
        increment(ev) {
          const row = $(ev.target).parents('tr');
          row.insertAfter(row.next());
        },
        decrement(ev) {
          const row = $(ev.target).parents('tr');
          row.insertBefore(row.prev());
        }
      }
      actions[$(ev.target).data('action')](ev);

      if (this.timer) {
        clearTimeout(this.timer);
      }

      this.timer = setTimeout(this.post, this.config.postDelay);
    }

    commit = data => {
      $(data.results).each((_index, item) => {
        this.rows.find(`[data-pk=${item.id}]`).data(
          'priority',
          item.priority
        );
      });
    }

    rollback = _error => {
      this.rows.parent('tbody').append(_parent =>
        this.rows.sort((a, b) =>
          this.getPriority(a) - this.getPriority(b)
        )
      );
    }

    freeze = () => {
      this.buttons.prop('disabled', true);
    }

    unfreeze = () => {
      this.buttons.prop('disabled', false);
    }

    post = () => {
      this.freeze();

      const request = $.ajax({
        url: this.config.postURL,
        method: 'POST',
        dataType: 'json',
        contentType: 'application/json',
        data: JSON.stringify(this.list),
        crossDomain: false,
        headers: {
          'X-CSRFToken': this.csrfToken
        }
      });

      request.done(this.commit);
      request.fail(this.rollback);
      request.always(this.unfreeze);
    }

  }


  function init() {
    return new SortableChangeList(
      $('#result_list'),
      SortableChangeListConfig.fromDOMNode(
        $('#media-priority-list-constants')
      )
    );
  }

  $(init);

}

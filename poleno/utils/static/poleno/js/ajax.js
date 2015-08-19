/* Perform AJAX request when clicked on an element or submitted a form with class ``ajax``.
 * Response data are returned by ``ajax-done`` event which is triggered on the element when
 * the request finishes. If the request fails, ``ajax-fail`` is triggered.
 *
 * Attributes:
 *     ``method``: Set HTTP method used for the request, e.g. "POST". If not specified
 *             GET method is used.
 *     ``action``, ``href``: Set request url.
 *     ``data-type``: Set AJAX response data type, e.g. "json" or "html".
 *
 * Requires:
 *  -- JQuery
 *
 * Example:
 *     <form class="ajax" method="post" action="...">...</form>
 *     <button class="ajax" action="...">...</button>
 *     <a class="ajax" href="..." method="post">...</a>
 *
 *     $('form').on('ajax-done', function(event, data){...})
 *     $('form').on('ajax-fail', function(event){...})
 */
$(function(){
	function handler(event){
		event.preventDefault();
		var type = $(this).attr('method') || 'get';
		var url = $(this).attr('action') || $(this).attr('href');
		var data = $(this).serialize();
		var dataType = $(this).data('type') || 'json';
		var that = this;
		$.ajax({
			type: type,
			url: url,
			data: data,
			dataType: dataType
		}).done(function(data){
			$(that).trigger('ajax-done', [data]);
		}).fail(function(){
			$(that).trigger('ajax-fail');
		});
		// See ``button_workaround`` below
		$(this).find('.ajax-button-workaround').remove();
	}
	$(document).on('submit', 'form.ajax', handler);
	$(document).on('click', ':not(form).ajax', handler);

	// Submit event does not know which submit button was clicked. Therefore we must
	// catch all clicks on such buttons and store their value in a hidden input. We
	// must remember to reset these values after the AJAX request is made, so they won't
	// mess with future submits.
	function button_workaround(event){
		var form = $(this).parents('form.ajax');
		var hidden = form.find('.ajax-button-workaround');
		if (hidden.length == 0) {
			hidden = $('<input class="ajax-button-workaround" type="hidden">').appendTo(form);
		}
		hidden.attr('name', $(this).attr('name'));
		hidden.attr('value', $(this).attr('value'));
	}
	$(document).on('click', 'form.ajax button[type="submit"]', button_workaround)
	$(document).on('click', 'form.ajax input[type="submit"]', button_workaround)
});

/* Takes data returned by an Ajax request and shows them in a modal. Then disables the Ajax
 * on the element and configures the modal to directly show given data on any further
 * clicks. After inserting returned data into the modal, emits ``dom-changed`` event on the
 * modal.
 *
 * Attributes:
 *     ``target``: Selector of modal element where to put response data. The element should
 *             have class ``modal``.
 *     ``fail-target``: Selector of modal element to show if the request fails.
 *
 * Example:
 *     <button class="ajax ajax-modal-once" action="..." target="#done" fail-target="#fail">...</button>
 *     <div id="done" class="modal hide fade">This will be replaced with response data</div>
 *     <div id="fail" class="modal hide fade">Ajax failed.</div>
 */
$(function(){
	function done(event, data){
		var target = $(this).data('target');
		$(target).html(data).trigger('dom-changed').modal('show');
		$(this).removeClass('ajax ajax-modal-once');
		$(this).attr('data-toggle', 'modal');
	}
	function fail(event){
		var target = $(this).data('fail-target');
		$(target).subModal();
	}
	$(document).on('ajax-done', '.ajax-modal-once', done);
	$(document).on('ajax-fail', '.ajax-modal-once', fail);
});

/* Takes data returned by an Ajax request and performs received operations. The response should be
 * a dictionary with two keys: ``result`` and ``operations``, where ``result`` should be the string
 * "operations" and ``operations`` should be a list of supported operations. If the request fails
 * a modal specified with ``fail-target`` attribute is opened.
 *
 * Supported operations:
 *
 *     {operation: 'content', target: <selector> | null, content: <html>}
 *         Replaces the ``target`` or the curent element inner html with new ``content``. After
 *         replacing its content, we emit ``dom-changed`` on the element.
 *
 *     {operation: 'redirect', localtion: <url>}
 *         Redirects to the given ``url``.
 *
 *     {operation: 'close-modal'}
 *         Closes bootstrap modal. Note that execution of any further operations is delayed until
 *         the modal is closed.
 */
$(function(){
	function execute(ops){
		if (!ops.length) return;
		var op = ops[0];
		var next = function(){ execute(ops.slice(1)); };
		switch (op.operation) {
			case 'content':
				$(op.target || this).html(op.content).trigger('dom-changed');
				next();
				break;
			case 'redirect':
				window.location = op.location;
				next();
				break;
			case 'close-modal':
				$.hideBootstrapModal(next);
				break;
		}
	}
	function done(event, data){
		if (data.result != 'operations') return;
		execute(data.operations);
	}
	function fail(event){
		var target = $(this).data('fail-target');
		$(target).subModal();
	}
	$(document).on('ajax-done', '.ajax-operations', done);
	$(document).on('ajax-fail', '.ajax-operations', fail);
});

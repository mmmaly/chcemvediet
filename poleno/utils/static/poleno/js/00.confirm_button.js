/* Intercepts clicks on elements with class ``confirm`` and asks user if he is sure he
 * wants to proceed. Question to ask is read from ``data-confirm``.
 *
 * This function must be defined before any other function attaching handlers to events
 * we need to prevent if the user decides not to proceed.
 *
 * Requires:
 *  -- JQuery
 *
 * Example:
 *     <button type="submit" class="confirm" data-confirm="Are you sure?">Submit</button>
 */
$(function(){
	function attach(base){
		// The handler must be attached directly to the target element. If we were to wait
		// until the event bubbles down to the document element, some other handler might
		// have intercepted the event earlier while bubbling.
		$(base).find('.confirm').not('.hasConfirm').addClass('hasConfirm').on('click', function(event){
			var message = $(this).data('confirm');
			if (!confirm(message)) {
				event.preventDefault();
				event.stopImmediatePropagation();
			}
		});
	};
	$(document).on('dom-changed', function(event){ attach(event.target); }); // Triggered by: poleno/js/ajax.js
	attach(document);
});

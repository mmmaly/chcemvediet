/* Submit button with class ``pln-busy-on-submit`` gets disabled and marked with class ``pln-busy``
 * when its form is submitted, so the user sees the page is waiting for the server and does not
 * submit the form again. The button is enabled again when the browser shows the page from its
 * back/forward cache.
 *
 * Requires:
 *  -- JQuery
 *
 * Example:
 *     <form method="post">
 *       <button type="submit" class="btn pln-busy-on-submit">Continue</button>
 *     </form>
 */
$(function(){
	$(document).on('submit', 'form', function(event){
		var form = this;
		// Let other handlers cancel the submit first; disabling the button synchronously would
		// also drop its name and value from the submitted data.
		setTimeout(function(){
			if (event.isDefaultPrevented())
				return;
			var buttons = $(form).find('.pln-busy-on-submit');
			if (form.id)
				buttons = buttons.add($('.pln-busy-on-submit[form="' + form.id + '"]'));
			buttons.addClass('pln-busy').prop('disabled', true).attr('aria-busy', 'true');
		}, 0);
	});
	$(window).on('pageshow', function(event){
		if (event.originalEvent.persisted)
			$('.pln-busy').removeClass('pln-busy').prop('disabled', false).removeAttr('aria-busy');
	});
});

/* Attaches JQuery Datepicker to all elements (usually input boxes) with class
 * ``datepicker``. Datepicker is attached when the user focuses the element for the first
 * time. We cannot just attach it to elements with correct class when the page loads,
 * because some elements may be inserted to the page later, e.g. with AJAX. The Datepicker
 * is configured to have current locale.
 *
 * Requires:
 *  -- JQuery
 *  -- JQuery UI Datepicker
 *
 * Example:
 *     <input type="text" class="datepicker" value="12/31/2014">
 */
$(function(){
	$(document).on('focus', '.datepicker', function(event){
		if (!$(this).hasClass('hasDatepicker')) {
			var lang = $('html').attr('lang');
			$(this).datepicker($.datepicker.regional[lang == 'en' ? '' : lang]);
			$(this).datepicker('show');
		}
	});
});

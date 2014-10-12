/* Attaches JQuery Autocomplete to all elements (usually input boxes) with class
 * ``autocomplete``. Autocomplete is attached when the user focuses the element for the
 * first time. We cannot just attach it to elements with correct class when the page loads,
 * because some elements may be inserted to the page later, e.g. with AJAX. Autocomplete
 * source url must be given in ``data-autocomplete-url`` attribute.
 *
 * Requires:
 *  -- JQuery
 *  -- JQuery UI Autocomplete
 *
 * Example:
 *     <input type="text" class="autocomplete" data-autocomplete-url="/autocomplete/url">
 */
$(function(){
	$(document).on('focus', '.autocomplete', function(event){
		if (!$(this).hasClass('ui-autocomplete-input')) {
			var source = $(this).data('autocomplete-url');
			$(this).autocomplete({
				source: source,
				minLength: 2
			});
		} else {
			$(this).autocomplete("search");
		}
	});
});

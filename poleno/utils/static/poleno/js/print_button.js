/* Clicking on elements with class ``print`` prints element specified by ``data-target``
 * attribute.
 *
 * Requires:
 *  -- JQuery
 *  -- JQuery PrintArea
 *
 * Example:
 *     <button type="button" class="print" data-target="#print-area">Print</button>
 *     <div id="#print-area">...</div>
 */
$(function(){
	$(document).on('click', '.print', function(event){
		event.preventDefault();
		var target = $(this).data('target');
		$(target).printArea();
	});
});

/* Clicking on element with class ``reload`` reloads the page.
 *
 * Requires:
 *  -- JQuery
 *
 * Example:
 *     <button type="button" class="reload">Reload</button>
 */
$(function(){
	$(document).on('click', '.reload', function(event){
		event.preventDefault();
		location.reload();
	});
});

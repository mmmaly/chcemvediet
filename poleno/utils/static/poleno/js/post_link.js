/* Makes every link with class ``post`` send POST request to its href URL when clicked.
 * Data for the request may be supplied by ``data-post-*`` element attributes.
 *
 * Requires:
 *  -- JQuery
 *
 * Example:
 *     <a href="/path/to/location" class="post" data-post-name="value">...</a>
 */
$(function(){
	$(document).on('click', 'a.post', function(event){
		event.preventDefault();
		var form = $('<form action="" method="post" style="display: none;"></form>');
		form.attr('action', $(this).attr('href'));

		$.each(this.attributes, function(){
			if (this.name.substring(0, 10) == "data-post-") {
				var input = $('<input type="hidden" name="" value="">');
				input.attr('name', this.name.substring(10));
				input.attr('value', this.value);
				input.appendTo(form);
			}
		});

		form.appendTo('body');
		form.submit();
	});
});

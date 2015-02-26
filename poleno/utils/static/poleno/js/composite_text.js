/* Required for ``poleno.utils.forms.CompositeText`` form widget.
 */
$(function(){
	$(document).on('focusin', '.composite-text', function(){
		$(this).addClass('focus');
	})
	$(document).on('focusout', '.composite-text', function(){
		$(this).removeClass('focus');
	})
});

/* Scrolls to selected element. If there is no such element, do nothing.
 *
 * Requires:
 *  -- JQuery
 *
 * Example:
 *     $('#element').scrollTo()
 */
$(function(){
	$.fn.scrollTo = function(){
		if (this.length) {
			var skip = parseInt($('body').css('padding-top'));
			var top = this.offset().top - skip;
			$('html, body').animate({
				scrollTop: top
			}, 200);
		}
	};
});

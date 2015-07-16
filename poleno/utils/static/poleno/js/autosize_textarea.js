/* Enables textarea to automatically adjust its height to its content.
 *
 * Requires:
 *  -- JQuery
 *
 * Example:
 *     <textarea class="autosize"></textarea>
 */
$(function(){
	function autosize(){
		$(this).css({
			'height': 'auto',
			'overflow-y': 'hidden',
		}).height(this.scrollHeight);
	};
	function autosizeAll(){
		$('textarea.autosize').each(autosize);
	};
	$(document).on('input', 'textarea.autosize', autosize);
	$(document).on('dom-changed', autosizeAll); // Triggered by: poleno/js/ajax.js
	$(window).on('resize', autosizeAll);
	autosizeAll();
});

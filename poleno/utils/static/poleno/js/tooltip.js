/* Enabled Bootstrap tooltips for elements with ``with-tooltip`` class.
 *
 * Requires:
 *  -- JQuery
 *  -- Bootstrap 2
 *
 * Example:
 *     <a class="with-tooltip" href="..." data-toggle="tooltip" title="Tooltip content.">Go</a>
 */
$(function(){
	function tooltip(base){
		$(base).find('.with-tooltip').not('.hasTooltip').addClass('hasTooltip').each(function(){
			if ($(this).hasClass('tooltip-permanent')) {
				$(this).tooltip({trigger: 'manual'}).tooltip('show');
			} else {
				$(this).tooltip();
			}
		});
	};
	$(document).on('dom-changed', function(event){ tooltip(event.target); }); // Triggered by: poleno/js/ajax.js
	tooltip(document);
});

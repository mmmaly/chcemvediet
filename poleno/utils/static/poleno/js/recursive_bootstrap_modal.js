/* Bootstrap modals are not recursive by default. Use this function if you want to show
 * a submodal while already showing another modal.
 *
 * Requires:
 *  -- JQuery
 *  -- Bootstrap 2
 *
 * Example:
 *     $('#some-modal').modal('show');
 *     ...
 *     $('#another-modal').subModal();
 */
$(function(){
	$.fn.subModal = function(){
		var layers = $('.modal-backdrop');
		this.modal('show');
		this.css('z-index', parseInt(this.css('z-index')) + 30*layers.length);
		var backdrop = $('.modal-backdrop').not(layers);
		backdrop.css('z-index', parseInt(backdrop.css('z-index')) + 30*layers.length);
	};
});

/* Bootstrap modals are animated. This function closes any open modals, waits for the
 * animation and then call the given callback.
 *
 * Requires:
 *  -- JQuery
 *  -- Bootstrap 2
 *
 * Example:
 *     $.hideBootstrapModal(function(){ console.log('Modals closed.'); });
 */
$(function(){
	$.hideBootstrapModal = function(then){
		if ($('.modal.in').length) {
			$('body').on('hidden.hideBootstrapModal', '.modal', function(){
				$('body').off('.hideBootstrapModal');
				then();
			});
			$('.modal.in').modal('hide');
		} else {
			then();
		}
	};
});

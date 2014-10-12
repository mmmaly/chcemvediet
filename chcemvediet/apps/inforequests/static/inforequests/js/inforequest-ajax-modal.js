$(function(){
	$(document).on('ajax-done', '.inforequest-ajax-modal', function(event, data){

		if (data.result == 'invalid') {
			$(this).html(data.content).trigger('dom-changed');

		} else if (data.result == 'success' && data.print) {
			$('.modal.in').removeClass('fade').modal('hide');
			if (data.content) $('#content').html(data.content).trigger('dom-changed');
			if (data.scroll_to) $(data.scroll_to).scrollTo();
			$('#print-modal').html(data.print).modal('show');

		} else if (data.result == 'success') {
			$.hideBootstrapModal(function(){
				if (data.content) $('#content').html(data.content).trigger('dom-changed');
				if (data.scroll_to) $(data.scroll_to).scrollTo();
			});
		}
	});
	$(document).on('ajax-fail', '.inforequest-ajax-modal', function(event){
		$('#ajax-fail-modal').subModal();
	});
});

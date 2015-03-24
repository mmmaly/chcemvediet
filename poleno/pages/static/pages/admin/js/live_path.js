$(function(){
	function live_path(base){
		$(base).find('.live-path').not('.hasLivePath').addClass('hasLivePath').each(function(){
			var live = this;
			var field = $(live).data('field');
			$('#'+field).on('change focus blur', function(){
				update.call(live);
			});
			update.call(live);
		});
	}
	function update(){
		var live = this;
		var field = $(live).data('field');
		var old_value = $(live).data('value');
		var new_value = $('#'+field).val();
		if (new_value != old_value) {
			$(live).data('value', new_value);
			if ($(live).data('ajax')) {
				$(live).data('ajax').abort();
			}
			$(live).data('ajax', $.ajax({
				type: 'get',
				url: $(live).data('url')+'?'+$.param({'path': new_value}),
				dataType: 'html',
			}).done(function(data){
				$(live).html($(data).html());
			}).fail(function(){
				$(live).html('--');
			}));
		}
	}
	$(document).on('dom-changed', function(event){ live_path(event.target); });
	live_path(document);
});

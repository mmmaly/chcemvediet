$(function(){
	function live_field(base){
		$(base).find('.live-field').not('.hasLiveField').addClass('hasLiveField').each(function(){
			var live = this;
			$.each($(live).data('fields'), function(i, field){
				$('#id_'+field).on('change focus blur', function(){
					update.call(live);
				});
			})
			update.call(live);
		});
	}
	function update(){
		var live = this;
		var changed = false;
		var params = {};
		$.each($(live).data('fields'), function(i, field){
			var old_value = $(live).data('value-'+field);
			var new_value = $('#id_'+field).val();
			if (new_value != old_value) changed = true;
			$(live).data('value-'+field, new_value);
			params[field] = new_value;
		});
		if (changed) {
			if ($(live).data('ajax')) {
				$(live).data('ajax').abort();
			}
			$(live).find('a').css('visibility', 'hidden');
			$(live).data('ajax', $.ajax({
				type: 'get',
				url: $(live).data('url')+'?'+$.param(params),
				dataType: 'html',
			}).done(function(data){
				$(live).html($(data).html());
			}).fail(function(){
				$(live).html('--');
			}));
		}
	}
	$(document).on('dom-changed', function(event){ live_field(event.target); });
	live_field(document);

	// Intercept django function changing form fields.
	function proxy(obj, method){
		var original = obj[method];
		obj[method] = function(){
			res = original.apply(this, arguments);
			$('.hasLiveField').each(update);
			return res;
		}
	}
	proxy(window, 'dismissRelatedLookupPopup');
});

$(function(){
	// Opener
	function popup_path(base){
		$(base).find('.popup-path').not('.hasPopupPath').addClass('hasPopupPath').each(function(){
			var field = this;
			$('<a href="#">').append(
				$('<img>').attr('src', $(field).data('icon'))
			).on('click', function(event){
				var url = $(field).data('popup-url')+'?'+$.param({'popup': 1, 'target': $(field).attr('id')});
				window.open(url, 'popup-path', 'height=500,width=800,resizable=yes,scrollbars=yes');
			}).insertAfter($(field)).before(' ');
		});
	}
	$(document).on('dom-changed', function(event){ popup_path(event.target); });
	popup_path(document);

	// Popup
	$(document).on('click', '.popup-select', function(){
		var target = $(this).data('target');
		var value = $(this).data('value');
		window.opener.$('#'+target).val(value).change();
		window.close();
	})
});

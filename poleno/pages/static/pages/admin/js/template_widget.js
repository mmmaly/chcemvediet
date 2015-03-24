$(function(){
	var widget_count = 0;

	function template_widget(base){
		$(base).find('textarea.template-widget').removeClass('template-widget').each(function(){
			var target = 'preview' + (++widget_count);
			var form = $('<form method="post" style="display: none;">')
				.attr('target', target)
				.attr('action', $(this).data('url'))
				.append($('<input type="hidden" name="csrfmiddlewaretoken">').val($.cookie('csrftoken')))
				.append($('<textarea name="template">').val($(this).val()))
				.appendTo($('body'));
			var widget = $('<div class="template-widget">')
				.insertAfter($(this))
				.append($('<div>').append($(this)))
				.append($('<div>').append($('<iframe>').attr('name', target)))
				.split({orientation: 'vertical', limit: 0})
				.resizable({handles: 's'})
				.after($('<button type="button" class="button" style="float: right;">Refresh Preview</button>').click(function(){
					form.find('textarea').val(widget.find('textarea').val());
					form.submit();
				}));
			form.submit();
		});
	}
	$(document).on('dom-changed', function(event){ template_widget(event.target); });
	template_widget(document);
});

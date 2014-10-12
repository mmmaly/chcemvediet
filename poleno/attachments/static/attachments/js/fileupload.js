/* Attaches JQuery File Upload to file inputs with class ``fileupload``.
 *
 * Attributes:
 *  -- data-url: URL where the files upload to.
 *  -- data-field: Hidden input box where to keep the list of uploaded files.
 *  -- data-target: Container where to show the list of uploaded files. The target should
 *         contain a hidden child with class ``fileupload-template`` which content will be
 *         used as a template for the list of uploaded files.
 *
 * FIXME: Instead ``fileupload-template`` child use Django-pipilene JS templates.
 *
 * Requires:
 *  -- JQuery
 *  -- JQuery File Upload
 *  -- JQuery Cookie
 *
 * Example:
 *     <input class="fileupload" type="file" name="files" multiple data-url="..." data-field="#field" data-target="#target">
 *
 *     <span id="target">
 *       <span class="fileupload-template hide">...</span>
 *     </span>
 *
 *     <form>
 *       ...
 *       <input id="field" type="hidden" name="...">
 *       ...
 *     </form>
 */
$(function(){
	function attach(base){
		$(base).find('.fileupload').not('.hasFileupload').addClass('hasFileupload').each(function(){
			var target = $(this).data('target');
			var field = $(this).data('field');
			$(target).data('field', field);
			$(this).fileupload({
				dataType: 'json',
				singleFileUploads: false,
				formData: {'csrfmiddlewaretoken': $.cookie('csrftoken')},
			})
		});
	};
	$(document).on('fileuploaddone', '.fileupload', function(event, data){
		var target = $(this).data('target');
		var field = $(this).data('field');
		var template = $(target).find('.fileupload-template');
		data.result.files.forEach(function(file){
			var label = $($(template).html());
			$(label).data('attachment', file.pk);
			$(label).find('a').attr('href', file.url).html(file.name);
			$(target).append(label).append(' ');
			$(field).val($(field).val() + ',' + file.pk + ',');
		});
	});
	$(document).on('click', '.fileupload-label-close', function(event){
		var label = $(this).parents('.fileupload-label');
		var attachment = $(label).data('attachment');
		var target = $(label).parent();
		var field = $(target).data('field');
		$(label).hide(300, function(){ $(this).remove(); });
		$(field).val($(field).val().replace(','+attachment+',', ','));
	});
	$(document).on('dom-changed', function(event){ attach(event.target); }); // Triggered by: poleno/js/ajax.js
	attach(document);
});

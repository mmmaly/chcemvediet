$(function(){
	$('.fixed').each(function(){
		$(this).clone().insertAfter($(this)).addClass('phantom');
	});
});

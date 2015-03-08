$(function(){
	// Fix dropdown panel not to close when clicked.
	$('body').on('click', '.dropdown-panel', function(event){
		event.stopPropagation();
	});
});

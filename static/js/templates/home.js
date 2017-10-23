$(document).ready(function(){

	function showMore(target){
		
		var table_id = $(target).attr('for')

		$('.table_polls tr:nth-child(n+12)').slideUp();		
		$('#'+table_id+' tr:nth-child(n+12)').slideDown();

		//Se elimina el evento de todos los demas botones "mostrar"
		$(".btn-toggle-show").off('click');

		//Se ponen todos los botones en modo "mostrar mas"
		$(".btn-toggle-show").on('click', function(event){
			showMore(event.target);
		})

		//Este boton en concreto se pone en modo "mostrar menos"
		$(target).off('click');
		$(target).on('click', function(event){
			showLess(target);
		})


	}

	function showLess(target){
		$('#'+table_id+' tr:nth-child(n+12)').slideUp();

		$(target).off('click');
		$(target).on('click', function(event){
			showMore(target);
		})
	}

	try {
		$('#table_available_polls tr:nth-child(n+12)').hide();
		$('#table_completed_polls tr:nth-child(n+12)').hide();
		$('#table_ongoing_polls tr:nth-child(n+12)').hide();

		$(".btn-toggle-show").on('click', function(event){
			showMore(event.target);
		})

	catch(err){

	}

})
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
		$(target).html("Show Less")


	}

	function showLess(target){
		var table_id = $(target).attr('for')


		$('#'+table_id+' tr:nth-child(n+12)').slideUp();

		$(target).off('click');
		$(target).on('click', function(event){
			showMore(target);
		})
		$(target).html("Show More")
	}


	// Si la tablas tablas tienen más de 10 filas, oculto las restantes y se muestra el boton para ocultar/mostrar
	try {
		$('#table_published_polls tr:nth-child(n+12)').hide();
		$('#table_draft_polls tr:nth-child(n+12)').hide();
		$('#table_archived_polls tr:nth-child(n+12)').hide();

		$(".btn-toggle-show").on('click', function(event){
			showMore(event.target);
		})

	} catch(err){

	}

	// Trigger del modal para invitar a la encuesta
	$(".invite-poll").on('click', function(){
		$("#inviteForm").modal('show')

		poll_pk = $(this).attr("for")
		$("#inviteForm form").attr("action", "/polls/send-poll/"+poll_pk+"/")
	})













})

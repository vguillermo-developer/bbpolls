$(document).ready(function(){

    $(".increase-order").on('click', function(){
        params = $(this).attr("for").split("_")
        poll_pk = params[0]
        question_pk = params[1]
        console.log("/polls/manage-poll/"+poll_pk+"/increase-question-order/"+question_pk+"/"+$("body").scrollTop()+"/")
        window.location.href = "/polls/manage-poll/"+poll_pk+"/increase-question-order/"+question_pk+"/"+$("body").scrollTop()+"/"
    })

    $(".decrease-order").on('click', function(){
        params = $(this).attr("for").split("_")
        poll_pk = params[0]
        question_pk = params[1]
        console.log("/polls/manage-poll/"+poll_pk+"/increase-question-order/"+question_pk+"/"+$("body").scrollTop()+"/")
        window.location.href = "/polls/manage-poll/"+poll_pk+"/decrease-question-order/"+question_pk+"/"+$("body").scrollTop()+"/";
    })
})
/*function cloneMore(selector, type) {
    var newElement = $(selector).clone(true);
    var total = $('#id_' + type + '-TOTAL_FORMS').val();
	 alert(newElement.find(':input').length)
    newElement.find(':input').each(function() {
        var name = $(this).attr('name').replace('-' + (total-1) + '-','-' + total + '-');
        var id = 'id_' + name;
        $(this).attr({'name': name, 'id': id}).val('').removeAttr('checked');
    });
    newElement.find('label').each(function() {
        var newFor = $(this).attr('for').replace('-' + (total-1) + '-','-' + total + '-');
        $(this).attr('for', newFor);
    });
    total++;
    $('#id_' + type + '-TOTAL_FORMS').val(total);
    $(selector).after(newElement);
}*/

function set_functions() {
        $('.add-question').click(function() {
    	    return addQuestion();
        });
        $('.delete-question').click(function() {
    	    return deleteForm(this, "question");
		});

		$('.add-choice').click(function() {
			return addChoice(this)		
		});

        $('.delete-choice').click(function() {
    	    return deleteForm(this, "choice");
		});

}

function updateQuestion(row, new_index) {	
		
	var legend = $(row).children(".legend")
	
	if (new_index == null)
		new_index = parseInt(legend.html().match(/\d+/))		
	
	legend.html(legend.html().replace(/\d+/, new_index+1))

    $(row).children().each(function() {
		if (this.id) this.id = this.id.replace(/\d+/, new_index)
		if (this.name) this.name = this.name.replace(/\d+/, new_index)
	});
	
}

function updateFormset(formset, form_sel){
	if (form_sel == "question")	
		fields = $(formset).children(".question-form")
	else if (form_sel == "choice")
		fields = $(formset).children(".choice-form")

	for (new_index=0; new_index<fields.length; new_index++){
		field = fields[new_index]
		updateForm(field, new_index, form_sel)
	}
	
}

function updateForm(field, new_index, form_sel){
	if (form_sel == "question")
		updateQuestion(field, new_index)
	else if (form_sel == "choice")
		updateChoice(field, false, new_index)
}	

function addQuestion() {

    var question = $('.question-form:last').clone(true)
	var choice = $(question).find('.choice-form:first').clone(true)
	
	$(choice).find(':input[type=text]').each(function(){
		this.value = "";
	})
	$(question).find('.choice-form').each(function(){
		$(this).remove()
	})
	
	updateChoice(choice, true)	
	updateQuestion(question)

    $(question).appendTo('.dynamic-question-form')
	$(choice).appendTo($(question).find(".dynamic-choice-form"))

    return false;
}

function updateChoice(row, new_question, choice_id){
	

	if (new_question == true)	
		choice_id = 0
	else if (choice_id == null){
		new_question = false
		choice_id = parseInt($(row).find(':input').get(0).id.match(/_-\d+-(\d+)-/)[1])+1
	} else
		new_question = false
	

	$(row).find('.legend').html($(row).find('.legend').html().replace(/\d+/, choice_id+1))
	
	if (new_question) {
		new_index = parseInt($(row).find(':input').get(0).id.match(/_-(\d+)-\d+-/)[1])-1
		$(row).find(':input').each( function() {
			this.id = this.id.replace(/_-\d+-\d+-/,"_-"+new_index+"-"+choice_id+"-")
			this.name = this.name.replace(/_-\d+-\d+-/,"_-"+new_index+"-"+choice_id+"-")
		})
	} else {
		$(row).find(':input').each( function() {
			this.id = this.id.replace(/_-(\d+)-\d+-/,"_-$1-"+(choice_id)+"-")
			this.name = this.name.replace(/_-(\d+)-\d+-/,"_-$1-"+(choice_id)+"-")
		})
	}
}

function addChoice(btn){
	var row = $(btn).parent().parent().find('.dynamic-choice-form').find('.choice-form:last').clone(true)

	updateChoice(row)
	$(row).appendTo($(btn).parent().parent().find('.dynamic-choice-form'))
	
	return false
}

function deleteForm(btn, form_sel){
	var formset = $(btn).parent().parent()
	
	if ($(btn).parent().hasClass("choice-form"))
		form_sel = "choice"
	else
		form_sel = "question"

	if (formset.children(".question-form").length==1){
		$(btn).parent().find(":input[type=text]").each(function (){
			$(this).val("")
		})
	}else if (formset.children(".choice-form").length==1){
		$(btn).parent().find(":input[type=text]").each(function (){
			$(this).val("")
		})
	}else{
		$(btn).parent().remove()
		updateFormset(formset, form_sel)
		
	}
	
	return false
}



/*function deleteQuestion(btn, prefix) {
    $(btn).parents('.dynamic-form').remove();
    var forms = $('.dynamic-form');
    $('#id_' + prefix + '-TOTAL_FORMS').val(forms.length);
    for (var i=0, formCount=forms.length; i<formCount; i++) {
	    $(forms.get(i)).children().not(':last').children().each(function() {
	        updateQuestion(this, prefix, i);
	    });
    }
    return false;
}

/*

-------------------- CHOICES ------------------------

function updateQuestion(el, prefix, ndx) {
	var id_regex = new RegExp('(' + prefix + '-\\d+)');
	var replacement = prefix + '-' + ndx;
	if ($(el).attr("for")) $(el).attr("for", $(el).attr("for").replace(id_regex, replacement));
	if (el.id) el.id = el.id.replace(id_regex, replacement);
	if (el.name) el.name = el.name.replace(id_regex, replacement);
}

function addQuestion(btn, prefix) {
    var formCount = parseInt($('#id_' + prefix + '-TOTAL_FORMS').val());
    var row = $('.dynamic-form:last').clone(true).get(0);

    $('.dynamic-question-form').append($(row).removeAttr('id'))
    $(row).children().not(':last').children().each(function() {
	    updateQuestion(this, prefix, formCount);
	    $(this).val('');
    });
    $(row).find('.delete-row').click(function() {
	    deleteForm(this, prefix);
    });
    $('#id_' + prefix + '-TOTAL_FORMS').val(formCount + 1);
	
	set_functions();
    return false;
}

function deleteQuestion(btn, prefix) {
    $(btn).parents('.dynamic-form').remove();
    var forms = $('.dynamic-form');
    $('#id_' + prefix + '-TOTAL_FORMS').val(forms.length);
    for (var i=0, formCount=forms.length; i<formCount; i++) {
	    $(forms.get(i)).children().not(':last').children().each(function() {
	        updateQuestion(this, prefix, i);
	    });
    }
    return false;
}*/

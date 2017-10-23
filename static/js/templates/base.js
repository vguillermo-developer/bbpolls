// NOTIFICATION TEMPLATE WITH ITS DEFAULT VALUES
/*$.notify({
	// options
	icon: 'glyphicon glyphicon-warning-sign',
	title: 'Bootstrap notify',
	message: 'Turning standard Bootstrap alerts into "notify" like notifications',
	url: 'https://github.com/mouse0270/bootstrap-notify',
	target: '_blank'
},{
	// settings
	element: 'body',
	position: null,
	type: "info",
	allow_dismiss: true,
	newest_on_top: false,
	showProgressbar: false,
	placement: {
		from: "top",
		align: "right"
	},
	offset: 20,
	spacing: 10,
	z_index: 1031,
	delay: 5000,
	timer: 1000,
	url_target: '_blank',
	mouse_over: null,
	animate: {
		enter: 'animated fadeInDown',
		exit: 'animated fadeOutUp'
	},
	onShow: null,
	onShown: null,
	onClose: null,
	onClosed: null,
	icon_type: 'class',
	template: '<div data-notify="container" class="col-xs-11 col-sm-3 alert alert-{0}" role="alert">' +
		'<button type="button" aria-hidden="true" class="close" data-notify="dismiss">×</button>' +
		'<span data-notify="icon"></span> ' +
		'<span data-notify="title">{1}</span> ' +
		'<span data-notify="message">{2}</span>' +
		'<div class="progress" data-notify="progressbar">' +
			'<div class="progress-bar progress-bar-{0}" role="progressbar" aria-valuenow="0" aria-valuemin="0" aria-valuemax="100" style="width: 0%;"></div>' +
		'</div>' +
		'<a href="{3}" target="{4}" data-notify="url"></a>' +
	'</div>' 
});*/

function setErrorMessage(msg){
	$.notify({
		// options
		icon: 'glyphicon glyphicon-warning-sign',
		message: msg,
	},{
		// settings
		position: 'fixed',
		offset: {
			x:20,
			y:130
		},
		type: "danger",
		delay: 7000,
		mouse_over: 'pause'
	});
}

function setWarningMessage(msg){
	$.notify({
		// options
		icon: 'glyphicon glyphicon-warning-sign',
		message: msg,
	},{
		// settings
		position: 'fixed',
		offset: {
			x:20,
			y:130
		},
		type: "warning",
		delay: 7000,
		mouse_over: 'pause'
	});
}


function setSuccessMessage(msg){
	$.notify({
		// options
		icon: 'glyphicon glyphicon-thumbs-up',
		message: msg,
	},{
		// settings
		position: 'fixed',
		offset: {
			x:20,
			y:130
		},
		type: "success",
		delay: 7000,
		mouse_over: 'pause'
	});
}

function setInfoMessage(msg){
	$.notify({
		// options
		icon: 'glyphicon glyphicon-info-sign',
		message: msg,
	},{
		// settings
		position: 'fixed',
		offset: {
			x:20,
			y:130
		},
		type: "info",
		delay: 7000,
		mouse_over: 'pause'
	});
}
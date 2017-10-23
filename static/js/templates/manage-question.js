$(document).ready(function() {

function setMultimediaInfo(selected_media){
    $('.multimedia-content-info').hide()
    switch(selected_media){
        case "IMAGE":
            $('.image-info').show()
            $('.table-mm-src tr td').removeClass('warning')
            $('.table-mm-src tr.row-image-src td:nth-child(1)').addClass('warning')
            $('.table-mm-src tr.row-image-src td:nth-child(2)').addClass('warning')
            $('.table-mm-src tr.row-image-src td:nth-child(3)').addClass('warning')
            break;
        case "AUDIO":
            $('.audio-info').show()
            $('.table-mm-src tr td').removeClass('warning')
            $('.table-mm-src tr.row-audio-src td:nth-child(1)').addClass('warning')
            $('.table-mm-src tr.row-audio-src td:nth-child(2)').addClass('warning')
            $('.table-mm-src tr.row-audio-src td:nth-child(3)').addClass('warning')
            break;
        case "VIDEO":
            $('.video-info').show()
            $('.table-mm-src tr td').removeClass('warning')
            $('.table-mm-src tr.row-video-src td:nth-child(1)').addClass('warning')
            $('.table-mm-src tr.row-video-src td:nth-child(2)').addClass('warning')
            $('.table-mm-src tr.row-video-src td:nth-child(3)').addClass('warning')
            break;
        case "IFRAME":
            $('.iframe-info').show()
            $('.table-mm-src tr td').removeClass('warning')
            $('.table-mm-src tr.row-iframe-src td:nth-child(1)').addClass('warning')
            $('.table-mm-src tr.row-iframe-src td:nth-child(2)').addClass('warning')
            $('.table-mm-src tr.row-iframe-src td:nth-child(3)').addClass('warning')
            break;
        default:
            $('.none-info').show()
            $('.table-mm-src tr td').removeClass('warning')
            break;
    }
}

//First hide everything except the media type selected
$('.multimedia-content-info').hide()
selected_media = $('#id_media_content').val()
    switch(selected_media){
        case "IMAGE":
            $('.image-info').show()
            $('.table-mm-src tr td').removeClass('warning')
            $('.table-mm-src tr.row-image-src td:nth-child(1)').addClass('warning')
            $('.table-mm-src tr.row-image-src td:nth-child(2)').addClass('warning')
            $('.table-mm-src tr.row-image-src td:nth-child(3)').addClass('warning')
            break;
        case "AUDIO":
            $('.audio-info').show()
            $('.table-mm-src tr td').removeClass('warning')
            $('.table-mm-src tr.row-audio-src td:nth-child(1)').addClass('warning')
            $('.table-mm-src tr.row-audio-src td:nth-child(2)').addClass('warning')
            $('.table-mm-src tr.row-audio-src td:nth-child(3)').addClass('warning')
            break;
        case "VIDEO":
            $('.video-info').show()
            $('.table-mm-src tr td').removeClass('warning')
            $('.table-mm-src tr.row-video-src td:nth-child(1)').addClass('warning')
            $('.table-mm-src tr.row-video-src td:nth-child(2)').addClass('warning')
            $('.table-mm-src tr.row-video-src td:nth-child(3)').addClass('warning')
            break;
        case "IFRAME":
            $('.iframe-info').show()
            $('.table-mm-src tr td').removeClass('warning')
            $('.table-mm-src tr.row-iframe-src td:nth-child(1)').addClass('warning')
            $('.table-mm-src tr.row-iframe-src td:nth-child(2)').addClass('warning')
            $('.table-mm-src tr.row-iframe-src td:nth-child(3)').addClass('warning')
            break;
        case "NONE":
            $('.none-info').show()
            $('.table-mm-src tr td').removeClass('warning')
            break;
    }


//Listener for multimedia content selector
$('#id_media_content').on('change', function(event){
    setMultimediaInfo($(this).val())
})



});
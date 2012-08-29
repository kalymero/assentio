/* Handle the disabled features */
$(".disabled_feature").hover(function(){ $(this).css('outline','2px dotted red'); },
                             function(){$(this).css('outline','None'); }
                             );
$(".disabled_feature").tooltip({title: "This feature is not yet implemented. Please try again in a while!", placement:"bottom"});


/* Apply the "active" class to the context page */
var post_id = $("#post-id").attr("data-id");
var focused = false;

$(".nav li a").each(function(index){
    
    if ($(this).attr("href").replace('/post/', '') == post_id){
        $(this).parent().addClass("active");
        focused = true;
    }

    });

if (!focused) {
    $("#home").addClass("active");
}

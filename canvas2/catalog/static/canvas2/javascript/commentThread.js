var ideaPK;
var canvasPK;

$j(document).ready(function(data){
    $j.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!(/^http:.*/.test(settings.url) || /^https:.*/.test(settings.url))) {
                // Only send the token to relative URLs i.e. locally.
                xhr.setRequestHeader("X-CSRFToken", getCookie("csrftoken"));
            }
        }
    });

    var url = window.location.pathname;
    var splitURL = url.split("/");
    ideaPK = splitURL[splitURL.length -2];

    data = {
        "idea_pk": ideaPK
    };

    performAjaxPOST(url, data, initSuccessCallback, initFailureCallback);
});

/*************************************************************************************************************
**************************************************************************************************************
                                            EVENT HANDLERS
**************************************************************************************************************   
**************************************************************************************************************/
$j("#add-comment").submit(function(e){
/*
    Handler for adding a comment
*/
    e.preventDefault();
    inputText = escapeChars($j(this).find("input[value]")[0].value);

    url = "/catalog/new_comment/";

    data = {
        "input_text": inputText,
        "idea_pk": ideaPK
    };
    performAjaxPOST(url, data, addCommentSuccessCallback, addCommentFailureCallback);
    $j(this).find("input[value]")[0].value = "";
    $j(this).find("input[placeholder]")[0].placeholder = "Type a comment";
});



$j(document).on("click", ".delete-comment", function(e){
    e.preventDefault();
    console.log("DELETE");
    url = "/catalog/delete_comment/";
    var commentDivID = $j(this).parent()[0].id;
    var commentPK = commentDivID.split("-")[1];

    // console.log(commentDivID);
    // console.log(commentPK);

    data = {
        "comment_pk": commentPK
    };

    performAjaxPOST(url, data, deleteCommentSuccessCallback, deleteCommentFailureCallback);
    $j('#'+commentDivID).remove();
});



$j("#resolve-comments").on("click", function(e){

    e.preventDefault();
    var comments = $j("#comment-thread").children();
    // console.log(comments);
    url = "/catalog/delete_comment/";

    for (var i = 0; i < comments.length; i++){
        var commentPK = comments[i].children[0].id.split("-")[1];
        console.log(commentPK);
        data = { "comment_pk": commentPK };
        performAjaxPOST(url, data, deleteCommentSuccessCallback, deleteCommentFailureCallback);
        comments[i].remove();
    }    
    $j("#comment-thread").append("<p id='no-comment'>No Comments!</p>");
});


$j("#back").on("click", function(e){
    window.location.href = "/catalog/canvas/" + canvasPK + "/";
});
/*************************************************************************************************************
**************************************************************************************************************
                                            CALLBACK FUNCTIONS
**************************************************************************************************************   
**************************************************************************************************************/
function deleteCommentSuccessCallback(data){
}

function deleteCommentFailureCallback(data){
    console.log(data);
}

function addCommentSuccessCallback(data){
    comment = JSON.parse(data.comment);
    author = JSON.parse(data.author)
    console.log(comment);

    // remove the 'no comments!' stand-in
    $j("#no-comment").remove();

    $j("#comment-thread").append(
        "<li>                                                                                       \
            <div id = 'comment-"+ comment[0].pk+"'> " +
                comment[0].fields.text + "                                                          \
                <br/>                                                                               \
                <p> by " + author +
                    " at " + comment[0].fields.timestamp + 
                "</p>                                                                               \
                <button class = 'delete-comment'>Delete Comment</a>                                 \
            </div>                                                                                  \
        </li>" 
    );
}

function addCommentFailureCallback(data){
    console.log(data);
}

function initSuccessCallback(data){
    var comments = JSON.parse(data.comments);
    var users = data.authors;


    if (comments.length > 0) {
        for (var i = 0; i < comments.length; i++){
            $j("#comment-thread").append(
                "<li>                                                                                       \
                    <div class = 'comment-div' id = 'comment-"+ comments[i].pk+"'> " +
                        comments[i].fields.text + "                                                         \
                        <br/>                                                                               \
                        <p> by " + users[i] +
                            " at " + comments[i].fields.timestamp + 
                        "</p>                                                                               \
                        <button class = 'delete-comment'>Delete Comment</a>                                 \
                    </div>                                                                                  \
                </li>" 
            );
        }
    }
    else { 
        $j("#comment-thread").append("<p id='no-comment'>No Comments!</p>");
    }

}

function initFailureCallback(data){
    console.log(data);
}
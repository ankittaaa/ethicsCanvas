var ideaPK;

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
    comment = JSON.parse(data);

    // remove the 'no comments!' stand-in
    $j("#no-comment").remove();

    $j("#comment-thread").append(
        "<li>                                                                                       \
            <div id = 'comment-"+ comment[0].pk+"'> " +
                comment[0].fields.text + "                                                          \
                <br/>                                                                               \
                <p> by " + comment[0].fields.author_name +
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
    comments = JSON.parse(data);
    if (comments.length > 0) {
        for (var i = 0; i < comments.length; i++){
            $j("#comment-thread").append(
                "<li>                                                                                       \
                    <div id = 'comment-"+ comments[i].pk+"'> " +
                        comments[i].fields.text + "                                                         \
                        <br/>                                                                               \
                        <p> by " + comments[i].fields.author_name +
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
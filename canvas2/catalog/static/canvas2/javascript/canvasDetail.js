/*
****************
    GLOBALS       
****************
*/
var canvasPK;
var categories = [
    "Individuals Affected",
    "Groups Affected",
    "Behaviour",
    "Relations",
    "World Views",
    "Group Conflicts",
    "Product or Service Failure",
    "Problematic Use of Resources",
    "What can we do?",
    "Uncategorised"
];

$j(document).ready(function(data){
    $j.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!(/^http:.*/.test(settings.url) || /^https:.*/.test(settings.url))) {
                // Only send the token to relative URLs i.e. locally.
                xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
            }
        }
    });

    var url = window.location.pathname;
    var splitURL = url.split("/");
    canvasPK = splitURL[splitURL.length - 2];


    // INITIAL AJAX REQUEST TO GET CANVAS INFORMATION AND RENDER IT TO PAGE
    // data = {
    //     "canvas_pk": canvasPK
    // };
    performAjaxGET(url, initSuccessCallback, initFailureCallback);

});

/*************************************************************************************************************
**************************************************************************************************************
                                            EVENT HANDLERS
**************************************************************************************************************   
**************************************************************************************************************/

    
$j(document).on("submit", ".idea-form", function(e){
/*
    Handler for editing of an idea, performs a POST and receives JSON response - this can be discarded as the text is already in the field 
    having been entered by user, and remains there on refresh

    Looks different to other event handlers as the elements it listens to are dynamically added 
*/
    e.preventDefault();
    inputText = escapeChars($j(this).find("input[value]")[0].value);
    // the $j(this).find() method doesn"t seem to work for idea_pk, which is a "list" attribute
    idea_pk = $j(this)[0][0].attributes[1].value;
    url = "/catalog/idea_detail/";

    data = {
        "input_text": inputText,
        "idea_pk": idea_pk
    };
    performAjaxPOST(url, data, editIdeaSuccessCallback, editIdeaFailureCallback);
});



$j(document).on("click", "#delete", function(e){
/*
    Handler for deleting an idea, performs a POST and receives JSON response 
    AND should remove the element from the DOM
*/
    e.preventDefault();
    idea_pk = $j(this)[0].attributes[1].value;

    url = "/catalog/delete_idea/";
    data = {
        "idea_pk": idea_pk
    };

    performAjaxPOST(url, data, deleteIdeaSuccessCallback, deleteIdeaFailureCallback);
    // delete list element with the matching list attribute
    $j("li[list = " + idea_pk + "]").remove();
});



$j(".new-idea").click(function(e){
/*
    Handler for addition of an idea, performs a POST and receives JSON response 
*/
    category = $j(".new-idea").index(this);
    e.preventDefault();

    url = "/catalog/new_idea/";
    data = {
        "canvas_pk": canvasPK,
        "category": category
    };
    performAjaxPOST(url, data, newIdeaSuccessCallback, newIdeaFailureCallback);
});



$j(document).on("click", ".comments", function(e){
/*
    Handler for opening the comment thread for the clicked idea
*/
    idea_pk = this.attributes[1].value;
    url = "/catalog/comment_thread/" + idea_pk + "/";
    window.location.href = url;
});



$j("#collaborators").on("click", function(e){
    url = "/catalog/collaborators/" + canvasPK + "/";
    window.location.href = url;
});


/*************************************************************************************************************
**************************************************************************************************************
                                            CALLBACK FUNCTIONS
**************************************************************************************************************   
**************************************************************************************************************/


function deleteIdeaSuccessCallback(data){
}

function deleteIdeaFailureCallback(data){
    console.log("Deletion Failed");
}

function newIdeaSuccessCallback(data){
/*
    Function to append a newly-created idea to the list of ideas
*/
    idea = JSON.parse(data);
    var listID = '#idea-list-' + idea[0].fields.category;

    $j(listID).append(
        "<li list = " + idea[0].pk +">                                                     \
            <form class = 'idea-form' action = ''>                                          \
                <input value = '' list = " + idea[0].pk + " placeholder = 'Add an idea'>    \
                <input type = 'submit' value = 'Submit'>                                    \
                <button id = 'delete' list = " + idea[0].pk + ">Delete Idea</button>        \
                <button class = 'comments' list = " + idea[0].pk + ">Comments</button>                                   \
            </form>                                                                         \
        </li>"
    );
}

function newIdeaFailureCallback(data){
    console.log(data);
}


function editIdeaSuccessCallback (data){
/* 
    Don't need to update anything, the text the user used to change the idea is
    still there thanks to the magic of AJAX (it will be rendered on refresh also)
*/ 
}

function editIdeaFailureCallback(data){
    console.log(data);
}

function initSuccessCallback(data){
/*
    This function is to pick apart the data received from the initial AJAX POST request, as there are several django models being sent back.
    I'll do something with these eventually, for now just having them extracted is enough. Decisions on which may be global or which are useful 
    at all remain undecided. 
*/  
            var ideas = JSON.parse(data.ideas);
            console.log(ideas);
            var tags = JSON.parse(data.tags);
            populateIdeaList(ideas);
}

function initFailureCallback(data){
    console.log(data);
}

function commentSuccessCallback(data){
    console.log("comment thread opened");
}

function commentFailureCallback(data){
    console.log(data);
}
/*************************************************************************************************************
**************************************************************************************************************
                                            MISCELLANEOUS
**************************************************************************************************************   
**************************************************************************************************************/


function populateIdeaList(ideas){
/*
    Function to handle the initial population of the canvas by writing received data to the DOM
*/
    for (var i = 0; i < ideas.length; i++){
        if (ideas[i].fields.text){
            // only do string manipulation if there's a string to manipulate
            var ideaString = ideas[i].fields.text;
            ideaString = escapeChars(ideaString);
            var listID = "#idea-list-" + ideas[i].fields.category;

            $j(listID).append(
                "<li list = " + ideas[i].pk +">                                                     \
                    <form class = 'idea-form' action = ''>                                          \
                        <input value = '" + ideas[i].fields.text + "' list = " + ideas[i].pk +">    \
                        <input type = 'submit' value = 'Submit'>                                    \
                        <button id = 'delete' list = " + ideas[i].pk + ">Delete Idea</button>       \
                        <button class = 'comments' list = " + ideas[i].pk + ">Comments</button>                                   \
                    </form>                                                                         \
                </li>"
            );
        }

        else {  // add a placeholder to the end of the input's attributes so I can continue to reference 'list' in edit-idea as normal
            $j(listID).append(
                "<li list = " + ideas[i].pk +">                                                     \
                    <form class = 'idea-form' action = ''>                                          \
                        <input value = '' list = " + ideas[i].pk + " placeholder = 'Add an idea'>   \
                        <input type = 'submit' value = 'Submit'>                                    \
                        <button id = 'delete' list = " + ideas[i].pk + ">Delete Idea</button>       \
                        <button class = 'comments' list = " + ideas[i].pk + ">Comments</button>                                   \
                    </form>                                                                         \
                </li>"
            );
        }
    }
}
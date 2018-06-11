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

// sortedIdeas will become a 2d array of objects. the 'i' indices will be the categories, while the  
// 'j' indices will be an object encapulating and idea and an array of its comments

var sortedIdeas = new Array(10);
var typingBools = new Array(10);
var typingUser = new Array(10);


var thisCanvas;
var tags = [];
var tagOccurrences = new Array();
var taggedCanvasses;
var ideas;
var comments;

var admins;
var adminNames = [];
var users;
var activeUsers = [];
var loggedInUser
var isAdmin;
var isAuth;

var publicCanvasses;
var privateCanvasses;
var selection;
var currentURL;

var tagButtons;
var collabComponent;
var ideaListComponent;

var trialIdeaSocket;
var ideaSocket;
var commentSocket;
var collabSocket;
var tagSocket;

var typingEntered = false;
// initialise this variable as a timeout handle
var typingTimer = setInterval(
            function(){console.log()}
            , 0);

window.clearTimeout(typingTimer);


$j(document).ready(function(data){


    $j.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!(/^http:.*/.test(settings.url) || /^https:.*/.test(settings.url))) {
                // Only send the token to relative URLs i.e. locally.
                xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
            }
        }
    });

    currentURL = window.location.pathname;
    var splitURL = currentURL.split("/");
    canvasPK = splitURL[splitURL.length - 2];
    var data = {
        "operation": " "
    };

    // INITIAL AJAX REQUEST TO GET CANVAS INFORMATION AND RENDER IT TO PAGE
    performAjaxGET(currentURL, data, initSuccessCallback, initFailureCallback);
});

/*************************************************************************************************************
**************************************************************************************************************
                                            EVENT HANDLERS
**************************************************************************************************************   
**************************************************************************************************************/

$j(document).on("select", ".idea-input", function(e){
/*
    Function to maintain the most recently selected piece of text
    for use by the create-tag button
*/
    var start = e.target.selectionStart;
    var end = e.target.selectionEnd;
    var wholeString = e.target.value;

    selection = wholeString.substr(start, end-start);
});
/*************************************************************************************************************
**************************************************************************************************************
                                            CALLBACK FUNCTIONS
**************************************************************************************************************   
**************************************************************************************************************/

/*************************************************************************************************************
                                                IDEA CALLBACKS
*************************************************************************************************************/


function deleteIdeaSuccessCallback(data){
    var i = JSON.parse(data.i);
    var tempCategory = JSON.parse(data.category);

    // grab a copy of the victim idea 
    var tempIdeaText = sortedIdeas[tempCategory][i].idea.fields.text;
    
    // search for tags that occur in the victim idea
    for (t in tags){
        if (tempIdeaText.includes(tags[t].fields.label))
            // decrement the tag if it occurs in the victim idea
            tagOccurrences[t]--;
        if (tagOccurrences[t] === 0){
            // delete the tag if it now does not occur 
            var thisTag = tags[t];

            tagSocket.send(JSON.stringify({
                'function': 'deleteTag',
                "tag_pk": thisTag.pk,
            }));
        }
    }

    // remove the victim {idea, [comments]} from the sorted ideas list
    sortedIdeas[tempCategory].splice(i, 1);
    typingBools[tempCategory].splice(i, 1);
    typingUser[tempCategory].splice(i, 1);
}

function deleteIdeaFailureCallback(data){
    console.log("Deletion Failed");
}

function newIdeaSuccessCallback(idea){
/*
    Function for updating the idea list for the modified category
    upon addition of new or deletion of current idea
*/
    var tempIdea = JSON.parse(idea);
    var tempCategory = tempIdea[0].fields.category;
    // console.log(tempIdea);
    // console.log(tempIdea[0]);

    // since ideas are sorted from newest to oldest, push the new idea to the front of sortedIdeas for the category
    // and an empty array for the comments, as a brand-new idea has no comments yet    
    if (sortedIdeas[tempCategory][0].idea === null)
    {
        // console.log("emptyCategory!")
        sortedIdeas[tempCategory].splice(0, 1, {
            idea: tempIdea[0],
            comments: []
        });
    }
    else
    {
        sortedIdeas[tempCategory].unshift({
            idea: tempIdea[0],
            comments: []
        });
    }   
    // console.log(sortedIdeas[tempCategory]);

    // if (isAuth === true){
        typingBools[tempCategory].unshift(false);
        typingUser[tempCategory].unshift('');
    // }
}

function newIdeaFailureCallback(data){
    console.log(data);
}


function editIdeaSuccessCallback (data){
    var inIdea = (JSON.parse(data.idea))[0];
    var tempCategory = inIdea.fields.category;
    var i = JSON.parse(data.i);
    sortIdeas(inIdea, i, tempCategory);
}

function editIdeaFailureCallback(data){
    console.log(data);
}


function typingCallback(data, f){
    // console.log(f);
    var tempCategory = data['category'];
    var tempName = data['username'];
    var i = data['i']
    // console.log("category: " + tempCategory);
    // console.log("idea: " + i);
    // do nothing, the logged in user knows when they're typing
    if (tempName == loggedInUser[0].fields.username)
        return;

    if (f === "typing"){
        // console.log(typingBools[tempCategory]);
        typingUser[tempCategory].splice(i, 1, tempName);
        typingBools[tempCategory].splice(i, 1, true);
        // console.log(typingBools[tempCategory]);
    }
    else {
        // console.log(typingBools[tempCategory]);
        typingUser[tempCategory].splice(i, 1, '');
        typingBools[tempCategory].splice(i, 1, false);
        // console.log(typingBools[tempCategory]);
    }



}
/*************************************************************************************************************
                                        COMMENT CALLBACKS
*************************************************************************************************************/


function addCommentSuccessCallback(data){
    var i = JSON.parse(data.i);
    var returnComment = JSON.parse(data.comment);
    var tempCategory = JSON.parse(data.category);
    sortedIdeas[tempCategory][i].comments.unshift(returnComment[0]);
}

function addCommentFailureCallback(data){
    console.log(data);
}


function deleteCommentSuccessCallback(data){
    // var parsedData = JSON.parse(data);
    var i = JSON.parse(data.i);
    var c = JSON.parse(data.c);
    var tempCategory = JSON.parse(data.category);

    sortedIdeas[tempCategory][i].comments.splice(c, 1);
}

function deleteCommentFailureCallback(data){
    console.log(data);
}


function resolveCommentSuccessCallback(data){
    var tempCategory = JSON.parse(data.category);
    var i = JSON.parse(data.i);

    // empty the comments for the idea
    var length = sortedIdeas[tempCategory][i].comments.length;

    for (var c = 0; c < length; c++)
        sortedIdeas[tempCategory][i].comments.pop();

    // ideaListComponent.ideaList = sortedIdeas;
    
    // ideaListComponent.$children[0].$children[tempCategory].$children[i].comments = [];

}
function resolveCommentFailureCallback(data){
    console.log(data);
}

/*************************************************************************************************************
                                            TAG CALLBACKS
*************************************************************************************************************/

function newTagSuccessCallback(data){
    // re-execute these steps so a new tag will, on being clicked, show it's in the current canvas
    var newTag = JSON.parse(data.tag);
    tags.unshift(newTag[0]);  
    tagOccurrences.unshift(0);
    thisCanvas.fields.tags = tags;
  
    publicCanvasses = JSON.parse(data.public);
    privateCanvasses = JSON.parse(data.private);
    populateTagList();


}

function newTagFailureCallback(data){
    console.log(data.responseText);
}

function deleteTagSuccessCallback(data){
    var i = JSON.parse(data.i);
    
    tagOccurrences.splice(i, 1);    
    tags.splice(i, 1);
    thisCanvas.fields.tags = tags;
    populateTagList();
}

function deleteTagFailureCallback(data){
    console.log(data.responseText);
}


/*************************************************************************************************************
                                        COLLABORATOR CALLBACKS
*************************************************************************************************************/

function addUserSuccessCallback(data){
    var tempUser = JSON.parse(data.user);
    users.push(tempUser[0]);
}

function addUserFailureCallback(data){
    console.log(data.responseText);
}

function deleteUserSuccessCallback(data){
    var ui = JSON.parse(data.ui);
    var victimIsAdmin = JSON.parse(data.victimIsAdmin);
    users.splice(ui, 1);

    if (victimIsAdmin === true){
        isAdmin = false;
        adminNames.splice(ui, 1);
        admins.splice(ui, 1);
    }
}

function deleteUserFailureCallback(data){
    console.log(data);
}

function promoteUserSuccessCallback(data){
    var tempAdmin = JSON.parse(data.admin);
    admins.push(tempAdmin[0]);
    adminNames.push(tempAdmin[0].fields.username);

    if (loggedInUser[0].fields.username === tempAdmin[0].fields.username)
    {
        // console.log(collabComponent.userIsAdmin);
        isAdmin = true;
        // console.log(collabComponent.userIsAdmin);
    }
}

function promoteUserFailureCallback(data){
    console.log(data.responseText);
}

function demoteAdminSuccessCallback(data){
    var ai = JSON.parse(data.ai);
    var victimName = adminNames[ai];
    admins.splice(ai, 1);
    adminNames.splice(ai, 1);

    if (loggedInUser[0].fields.username === victimName)
    {
        // console.log(collabComponent.userIsAdmin);
        isAdmin = false;
        // console.log(collabComponent.userIsAdmin);
    }
}

function demoteAdminFailureCallback(data){
    console.log(data.responseText);
}

function newActiveUserCallback(data){
    // console.log("Before addition: " + activeUsers);

    user = data.user;
    activeUsers.push(user[0].fields.username);

    collabSocket.send(JSON.stringify({
        'function': 'sendWholeList',
        'users': activeUsers,
    }));
}

function wholeListCallback(data){
    users = data.users;

    if (users.length <= activeUsers.length)
        return;
    else 
    {
        for (u in users){
            activeUsers.splice(u, 1, users[u]);
        }
    }
}

function removeActiveUserCallback(data){
    // console.log("Before removal: " + activeUsers);

    user = data.user;
    i = activeUsers.indexOf(user[0].fields.username);

    if (i > -1)
        activeUsers.splice(i, 1);
}


/*************************************************************************************************************
                                            INITIAL CALLBACK
*************************************************************************************************************/


function initSuccessCallback(data){
/*
    This function is to pick apart the data received from the initial AJAX POST request, as there are several django models being sent back.
    I'll do something with these eventually, for now just having them extracted is enough. Decisions on which may be global or which are useful 
    at all remain undecided. 
*/  
    // initially declare empty arrays for each index of sortedIdeas
    for (var i = 0; i < sortedIdeas.length; i++){
        sortedIdeas[i] = new Array();
        typingBools[i] = new Array();
        typingUser[i] = new Array();
    }

    comments = JSON.parse(data.comments);
    ideas = JSON.parse(data.ideas);
    tags = JSON.parse(data.tags);
    admins = JSON.parse(data.admins);
    users = JSON.parse(data.users);
    loggedInUser = JSON.parse(data.loggedInUser);
    
    if (loggedInUser.length === 0)
        isAuth = false;
    
    if (loggedInUser.length > 0) {
        isAuth = true;
        taggedCanvasses = new Array(tags.length);
        
        for (t in tags){
            tagOccurrences.push(0);
        }

        publicCanvasses = JSON.parse(data.public);
        privateCanvasses = JSON.parse(data.private);
        var allCanvasses = JSON.parse(data.allCanvasses);


        for (a in admins)
            adminNames.push(admins[a].fields.username);

        if (adminNames.indexOf(loggedInUser[0].fields.username) !== -1)
            isAdmin = true;
        else
            isAdmin = false;

        for (c in allCanvasses){
            if (allCanvasses[c].pk == canvasPK){
                thisCanvas = allCanvasses[c];
                break;
            }
        }
        populateTagList();
        initialiseSockets();
    }



    if (ideas.length > 0){
        for (idea in ideas){
            var ideaComments = [];
            for (comment in comments){
                if (comments[comment].fields.idea === ideas[idea].pk){
                    ideaComments.push(comments[comment]);
                }
            }
            if (loggedInUser.length > 0){
                for (t in tags){
                    // keep track of how many times a tag occurs. on deletion of all ideas containing the tag, the occurrences reaches
                    // 0 and the tag is removed 
                    if (ideas[idea].fields.text.includes(tags[t].fields.label))
                        tagOccurrences[t]++;
                }
            }

            sortedIdeas[ideas[idea].fields.category].push({
                idea: ideas[idea],
                comments: ideaComments
            });
            typingBools[ideas[idea].fields.category].push(false);
            typingUser[ideas[idea].fields.category].push('');
        }
    }
    else {
        for (s in sortedIdeas){
            sortedIdeas[s].push({
                idea: null,
                comments: []
            });
            typingBools[s].push(false);
            typingUser[s].push('');
        }
    }


    if (isAuth === true)
        $j('#canvas-title').html(thisCanvas.fields.title);
    else {
        $j('#canvas-title').html("Trial Canvas");

        // only want to initialise the ideaSocket so that new idea JSON objects can be acquired - NOT ADDED TO A CANVAS
        trialIdeaSocket = new WebSocket(
            'ws://' + window.location.host + 
            '/ws/canvas/' + canvasPK + '/trial-idea/'
        );

        trialIdeaSocket.onmessage = function(e){
            // console.log("Received");
            var data = JSON.parse(e.data);
            var idea = data['idea'];
            newIdeaSuccessCallback(idea);
        };
}

    tagButtons = new Vue({
        el: '#tag-div',
        data: {
            tagList: tags,
            canvasList: taggedCanvasses,
            show: false,
            showTag: true,
            auth: isAuth,
        },
    })

    ideaListComponent = new Vue({
        el: '#idea-div',
        data: {
            ideaList: sortedIdeas,
            categories: categories,
            isTyping: typingBools,
            typingUser: typingUser,
            auth: isAuth,
        }
    })

    collabComponent = new Vue({
        el: '#collab-div',
        data: {
            showCollab: false,
            usersList: users,
            adminsList: admins,
            adminNameList: adminNames,
            loggedInUser: loggedInUser,
            isAdmin: isAdmin,
            active: activeUsers,
            auth: isAuth,
        },
    })


    // console.log(loggedInUser);
}

function initFailureCallback(data){
    console.log(data);
}

/*************************************************************************************************************
**************************************************************************************************************
                                            VUE COMPONENTS
**************************************************************************************************************   
**************************************************************************************************************/

/*************************************************************************************************************
                                            IDEA-LIST COMPONENT
*************************************************************************************************************/


Vue.component('idea-list', {
    props: [],
    delimiters: ['<%', '%>'],
    
    data: function(){
        return {
            ideaList: sortedIdeas,
            categories: categories,
            isTyping: typingBools,
            typingUser: typingUser,
            auth: isAuth,
        }
    },

    template:'#ideas',
    
    computed: {
    },

    watch: {

    },
    
    methods: {

    },
    created: function(){
    }
})

/*************************************************************************************************************
                                            IDEA-ELEM COMPONENT
*************************************************************************************************************/
 
Vue.component('idea', {
    props: ['user', 'is-typing', 'ideas', 'index', 'categories', 'is-auth'],
    delimiters: ['<%', '%>'],
    
    data: function(){
        return {
            showComments: false,
            // Array of booleans for displaying individual modal components. As a single boolean, all modals will be rendered instead of the one for the comment thread of the clicked idea. 
            showCommentThread: new Array(this.ideas.length),
            isTypingBools: this.isTyping,
            typingUser: this.user,
        }
    },
    
    template:`  <div class="category-detail">\
                    <h3><% title() %></h3>\
                    \
                    <div  v-if="escapedIdeas[0]" >\
                        <div v-for="(idea, i) in escapedIdeas">\
                        \
                        <span>\
                            <input class="idea-input"\
                                type="text" :value="idea.fields.text"\
                                @blur="changed($event, idea, i)"\
                                @keydown="keydownCallback($event, idea, i)"\ 
                                @keypress="setTyping($event, idea, i)"\
                                @paste="setTyping($event, idea, i)"\
                                placeholder="Enter an idea"><p v-show="isTypingBools[i] == true"><%typingUser[i]%> is typing...</p>\
                        </span>\
                            </br>\
                            <button id="delete-idea" class="delete" @click="deleteIdea($event, idea, i)">Delete</button>\
                            <button v-if="isAuth" class="comments" v-on:click="displayMe(i)">Comments (<% commentList[i].length %>)</button>\
                            <button v-else class="comments" title="Sign up to use this feature" disabled>Comments</button>\
                            <comment v-show=showCommentThread[i] v-bind:commentList="commentList[i]" v-bind:idea="idea" v-bind:i="i" @close="displayMe(i)">\
                            </comment>\
                        </div>\
                        </br>\
                        \
                        \
                    </div>\
                    \
                    <button class="new-idea" @click="newIdea($event)">+</button>\
                    <button v-if="escapedIdeas[0]" class="new-tag" v-on:click="newTag()">Tag Selected Term</button>\
                    </br>\
                    </br>\
                </div>\
    `,
         
    computed: {
        category: function(){
            return categories[this.index]
        },

        ideaList: {
            get: function(){
                // console.log(this.ideas[0])
                var list = []

                
                // if (this.ideas[0] !== null){
                    if (this.ideas[0] !== null){
                        for (i in this.ideas){
                            list.push(this.ideas[i].idea)
                        }
                    }
                // }
                return list
            },

            set: function(ideasInput){
                var list = []
                if (this.ideasInput !== null){
                    for (i in this.ideasInput){
                        list.push(this.ideasInput[i].idea)
                    }
                }
                return list
            },
        },

        commentList: {
            get: function(){
                var list = []
                if (isAuth === true && this.ideas[0] !== null){
                    if (this.ideas[0].idea !== null){
                        for (i in this.ideas){
                            list.push(this.ideas[i].comments)
                        }
                    }
                }
                return list
            }
        },
        /* 
            using computed property to escape the html characters such as &apos as vue throws an 
            "invalid assignment left-hand side" error when I call the method directly with v-model, 
            the error not appearing until @change is triggered   
        */ 
        escapedIdeas: function(){
            var escaped = this.ideaList


            for (idea in escaped){
                if (escaped[idea] == null)
                    continue
                escaped[idea].fields.text = this.ideaString(escaped[idea])
            }
            return escaped
            
        },
    },

    methods: {

        displayMe(i){
        /*
            For setting an individual truth value to display a single modal component's comment thread, or to close it.
            This method is required as Vue doesn't detect array changes normally. 
        */
            Vue.set(this.showCommentThread, i, !this.showCommentThread[i])
        },

        currentIdeaComments(idea, comments){

            var returnComments = []
            if (isAuth === true){
                for (c in comments){
                    if (comments[c].fields.idea === idea.pk)
                    {   
                        returnComments.push(comments[c])
                    }
                }
            return returnComments
            }
        },

        close: function(){
            this.showCommentThread = false
        },

        displayComments: function(event, idea){
            // console.log(idea)
        },

        title: function(){
            return categories[this.index]
        },

        ideaString: function(idea){
            var string = escapeChars(idea.fields.text)
            // the following is to convert elements like &apos back to " ' " 
            var scratch = document.createElement("textarea")
            scratch.innerHTML = string

            return scratch.value
        },
        newIdea(event){
            // console.log(isAuth)

            if (isAuth === true)
            {
                ideaSocket.send(JSON.stringify({
                    'function': 'addIdea',
                    'category': this.index,
                }));
            }
            else {
                trialIdeaSocket.send(JSON.stringify({
                    // 'function': 'addIdeaTrial',
                    'category': this.index,
                }));
            }
        },

        deleteIdea(event, idea, i){
            if (isAuth === true){
                ideaSocket.send(JSON.stringify({
                    'function': 'deleteIdea',
                    'idea_pk': idea.pk,
                    'i': i
                }));
            }
            else
                sortedIdeas[this.index].splice(i, 1)
        },

        changed(event, idea, i){
            var text = escapeChars(event.target.value)
            text = text.replace(/[\t\s\n\r]+/g, " ")
            text = text.trim()

            if (isAuth === true){
                window.clearTimeout(typingTimer)
                
                ideaSocket.send(JSON.stringify({
                    'function': 'modifyIdea',
                    'input_text': text,
                    'idea_pk': idea.pk,
                    'category': this.index,
                    'i': i

                }));
                // if a user entered loads of whitespace, then replace current input field with trimmed text
                event.target.value = text
                idea.fields.text = text
                event.target.blur()
                typingTimer = window.setInterval(
                    setFalse.bind({isTyping: this.isTypingBools, vm: this, i: i, index: this.index})
                    , 0
                )
            }
            else {
                currIdea = sortedIdeas[this.index][i].idea
                currIdea.fields.text = text

                if (sortedIdeas[this.index].length > 1){
                    sortIdeas(currIdea, i, this.index)
                }
                else{
                    sortedIdeas[this.index].splice(i, 1, {
                        idea: currIdea,
                        comments: []
                    })
                }

            }

        },

        keydownCallback(event, idea, i){
            key = event.key
            
            if (key == "Enter")
                event.target.blur()

            if (key == "Escape")
                this.ideaList[i].fields.text = this.ideaList[i].fields.text
        },

        setTyping(event, idea, i){
            if (isAuth === true){

                window.clearTimeout(typingTimer)

                // only want to send something down the socket the first time this function is called
                if (typingEntered == false){        
                    ideaSocket.send(JSON.stringify({
                        'function': 'typing',
                        'category': this.index,
                        'username': loggedInUser[0].fields.username,
                        'i': i
                    }))
                }

                typingEntered = true

                // timeout function for clearing the <user> is typing message on other windows - waits 2s 
                typingTimer = window.setInterval(
                    setFalse.bind({isTyping: this.isTypingBools, vm: this, i: i, index: this.index})
                    , 2000
                )
            }
        },

        newTag(){
            if (isAuth === true){
                tagSocket.send(JSON.stringify({
                    'function': 'addTag',
                    "label": selection
                }));
                selection = ""
            }
        }

    },

    watch: {
        // commentList: function(){
        //     console.log(this.commentList)
        // }

    },   

    created: function(){
        for (var i = 0; i < this.showCommentThread.length; i++){
            this.showCommentThread[i] = false
        }
    },
})

/*************************************************************************************************************
                                            COMMENT COMPONENT
*************************************************************************************************************/
 
Vue.component('comment', {
    props: ['comment-list', 'show-comments', 'idea', 'i'],
    delimiters: ['<%', '%>'],
    
    data: function(){
        return {
            comments: this.commentList,
        }
    },
    
    template:'\
                <modal v-show="show">\
                \
                \
                    <div slot="header">\
                        <h3>Comments</h3>\
                        <input value="" placeholder = "Type a comment" @change="newComment($event)">\
                        <button>Post</button>\
                    </div>\
                \
                \
                    <div slot="body">\
                        <ul>\
                            <li v-for="(comment, c) in commentList" style="list-style-type:none;">\
                                <% commentString(comment) %>\
                                <button class="delete-comment" @click="deleteComment($event, comment, c)">Delete</button>\
                            </li>\
                        </ul>\
                    </div>\
                \
                \
                    <div slot="footer">\
                        <button class="resolve-comments" @click="resolveComments(idea)">Resolve All</button>\
                        <button class="modal-default-button" @click="$emit(\'close\')">Close</button>\
                    </div>\
                \
                \
                </modal>'
,
         
    computed: {
        currentIdea: function(){
            return this.idea
        },
        show: function(){
            return this.showComments
        },
        selfIndex: function(){
            return this.i
        }
    },
    
    watch: {
        // commentList: function(){
        //     console.log(this.commentList)
        // }

    },   

    methods: {
        commentString: function(comment){
            var string = escapeChars(comment.fields.text)
            // the following is to convert elements like &apos back to " ' " 
            var scratch = document.createElement("textarea")
            scratch.innerHTML = string

            return scratch.value
        },

        newComment(event){
            var text = escapeChars(event.target.value)
            event.target.value = ''
            text = text.replace(/[\t\s\n\r]+/g, " ")
            text = text.trim()
            
            commentSocket.send(JSON.stringify({
                'function': 'addComment',
                'input_text': text,
                'i': this.selfIndex,
                'idea_pk': this.currentIdea.pk
            }));
        },

        deleteComment(event, comment, c){
            commentSocket.send(JSON.stringify({
                'function': 'deleteComment',
                "comment_pk": comment.pk,
                'i': this.selfIndex,
                'c': c
            }));
        },

        resolveComments(idea){
            commentSocket.send(JSON.stringify({
                'function': 'resolveComments',
                "idea_pk": this.currentIdea.pk,
                'i': this.selfIndex,
            }));
        },
    },
})

/*************************************************************************************************************
                                            TAG-LIST COMPONENT
*************************************************************************************************************/
 
Vue.component('tag', {
    props: ['index', 'label'],
    delimiters:['<%', '%>'],

    data: function(){
        return {
            show: false,
            showTag: true,
            canvasList: taggedCanvasses,
            tagList: '',
            auth: isAuth,
        }
    },

    template: '#tag',

    // watcher for when the showTag data is changed by the emission of deleteTag by the 
    // tag-popup child element
    watch: {
        showTag: function(){
            var thisTag = tags[this.index]
            tags.splice(this.index, 1)
            data = {
                "tag_pk": thisTag.pk,
                "operation": "delete_tag"
            }
        },
    },

    methods: {
        tagInfo: function(event, index){
        },  
        exitTagInfo: function(event){
            // console.log('')
        }
    }
})

/*************************************************************************************************************
                                            TAG-ELEM COMPONENT
*************************************************************************************************************/
 
Vue.component('tag-popup', {
    props:['label', 'canvas', 'index'],
    delimiters: ['<%', '%>'],
    data: function(){
        return {
            c: ''
        }
    },

    template:'<modal>\
                <div slot="header">\
                <h3><% label %></h3>\
                <h4>Appears in: </h4>\
                </div>\
                <ul slot="body">\
                    <li v-for="c in canvasData" style="list-style-type:none;">\
                        <a v-bind:href="url(c)" target="_blank">\
                            <% c.fields.title %>\
                        </a>\
                    </li>\
                </ul>\
                \
                <div slot="footer">\
                    <button class="delete-tag" @click="deleteTag($event)">Delete</button>\
                    <button class="modal-default-button" @click="$emit(\'close\')">\
                    Close\
                    </button>\
                </div>\
            </modal>'
    ,

    computed: {
        canvasData: function(){
            return this.canvas
        }
    },

    methods:{
        url: function(c){
            return "/catalog/canvas/" + c.pk
        },
        deleteTag: function(event){
            tagSocket.send(JSON.stringify({
                'function': 'removeTag',
                'i': this.index,
                'tag_pk': tags[this.index].pk,
            }));
        }
    }

})

/*************************************************************************************************************
                                            COLLAB-LIST COMPONENT
*************************************************************************************************************/
 
Vue.component('collabs', {
    props: ['is-admin'],
    delimiters: ['<%', '%>'],
    
    template:'#collabs',

    data: function(){
        return {
            showCollab: false,
            usersList: users,
            adminsList: admins,
            adminNameList: adminNames,
            loggedInUser: loggedInUser,
            active: activeUsers,
            auth: isAuth,
        }
    },

    methods: {
    },
})

/*************************************************************************************************************
                                            COLLAB-POPUP COMPONENT
*************************************************************************************************************/
 
Vue.component('collab-popup', {
    props: ['users', 'admins', 'logged-in-user', 'is-admin', 'admin-names', 'active', 'auth'],
    delimiters: ['<%', '%>'],

    data: function(){
        return {
            currentUser: this.loggedInUser,
            name: '',
            a: '',
            c: '',
            activeList: this.active,
            isAuth: this.auth
        }
    },

    computed: {
        userList: function(){
            return this.users
        },
        adminList: function(){
            return this.admins
        },
        adminNameList: function(){
            return this.adminNames
        },
        admin: function(){
            return this.isAdmin
        }
    },

    template: `\
            <modal v-if="isAuth">\
                <div slot="header">\
                    <h3>Collaborators</h3>\
                </div>\
                \
                <div slot="body">\
                    <h3>Admins</h3>\
                        <ul>\
                        <li v-for="(a, ai) in adminList" style="list-style-type:none;">\
                            <span>\
                                <% a.fields.username\
                                + ( loggedInUser[0].fields.username === a.fields.username ? " (you)" : activeList.includes(a.fields.username) ? " (active)" : "" ) %>\
                            </span>\

                            <div \

                                id="admin-buttons"\
                                v-if="loggedInUser[0].fields.username !== a.fields.username && adminNameList.includes(loggedInUser[0].fields.username)"\
                            >\
                                <button class="delete-admin" @click="deleteUser($event, a, ai)">Delete</button>\
                                <button class="demote-admin" @click="demoteAdmin($event, a, ai)">Demote</button>\
                            </div>\
                        </li>\
                    </ul>\
                    \
                    <h3>Users</h3>\
                    <ul>\
                        <li v-for="(u, ui) in userList" style="list-style-type:none;">\
                            <span>\
                                <% u.fields.username  \
                                + ( loggedInUser[0].fields.username === u.fields.username ? " (you)" : activeList.includes(u.fields.username) ? " (active)" : "" ) %>\

                            </span>\
                            <div \
                                id="user-buttons"\
                                v-if="loggedInUser[0].fields.username !== u.fields.username && adminNameList.includes(loggedInUser[0].fields.username)"\
                            >\
                                <button class="delete-user" @click="deleteUser($event, u, ui)">Delete</button>\
                                <button \
                                    v-if="adminNameList.indexOf(u.fields.username) === -1"\
                                    class="promote-user" @click="promoteUser($event, u)"\
                                >Promote</button>\
                            </div>\
                        </li>\
                    </ul>\
                    <div v-if="adminNameList.includes(loggedInUser[0].fields.username)">\
                        <h3>Add User</h3>\
                        <input v-model="name" placeholder="Enter a username">\
                        <button @click="addUser($event, name, this.isAdmin)">Add User</button>\
                    </div>\
                </div>\
                \
                <div slot="footer">\
                    <button class="modal-default-button" @click="$emit(\'close\')">\
                    Close\
                    </button>\
                </div>\
            </modal>\
        `,

    methods: {
        addUser: function(event, name, isAdmin){
            // console.log(isAdmin);
            collabSocket.send(JSON.stringify({
                'function': 'addUser',
                'name': name
            }));
            this.name = ""
        },

        deleteUser: function(event, u, ui){
            collabSocket.send(JSON.stringify({
                'function': 'deleteUser',
                'user_pk': u.pk,
                'ui': ui
            }));
        },

        promoteUser: function(event, u){
            collabSocket.send(JSON.stringify({
                'function': 'promoteUser',
                'user_pk': u.pk,
            }));            
        },

        demoteAdmin: function(event, a, ai){
            collabSocket.send(JSON.stringify({
                'function': 'demoteUser',
                'user_pk': a.pk,
                'ai': ai
            }));
        },
    },
})

/*************************************************************************************************************
                                            MODAL COMPONENT
*************************************************************************************************************/
 
Vue.component('modal', {
  template: '#modal-template'
})

/*************************************************************************************************************
**************************************************************************************************************
                                            MISCELLANEOUS
**************************************************************************************************************   
**************************************************************************************************************/
function populateTagList(){
/*
    This function's purpose is to populate a 2D array of canvasses. Each 'i' element represents a tag,
    while the 'j' element represents the list of canvasses attached to that tag. 
*/
    var taggedPublic = [];
    var taggedPrivate = [];
    var tagged = [];

    for (var i = 0; i < tags.length; i++){

        // get a list of all public canvasses containing the current tag
        for (var j = 0; j < publicCanvasses.length; j++){
            if (publicCanvasses[j].fields.tags.includes(tags[i].pk)){
                taggedPublic.push(publicCanvasses[j]);
            }
        }

        // get a list of all private canvasses containing the current tag
        for (var j = 0; j < privateCanvasses.length; j++){
            if (privateCanvasses[j].fields.tags.includes(tags[i].pk)){
                taggedPrivate.push(privateCanvasses[j]);
            }
        }  

        tagged.push(taggedPublic);
        tagged.push(taggedPrivate);
        tagged = tagged[0].concat(tagged[1])

        taggedCanvasses.splice(i, 1, tagged);

        taggedPublic = [];
        taggedPrivate = [];
        tagged = [];
    }
}

function populateUsersAdmins(data){
/*
    Function for updating the user/admin list for the 
    collaborator component upon modification of either list
*/
    admins = JSON.parse(data.admins);

    collabComponent.adminsList = admins;
    collabComponent.$children[0].adminsList = admins;    

    users = JSON.parse(data.users);

    collabComponent.usersList = users;
    collabComponent.$children[0].usersList = users;

    adminNames = [];

    for (a in admins)
        adminNames.push(admins[a].fields.username);

    collabComponent.adminNameList = adminNames;
    collabComponent.$children[0].adminNameList = adminNames; 

}

function initialiseSockets(){

/********************************************************************
*********************************************************************
                        SOCKET DECLARATIONS
*********************************************************************                            
*********************************************************************/

    ideaSocket = new WebSocket(
        'ws://' + window.location.host + 
        '/ws/canvas/' + canvasPK + '/idea/'
    );

    commentSocket = new WebSocket(
        'ws://' + window.location.host + 
        '/ws/canvas/' + canvasPK + '/comment/'
    );

    collabSocket = new WebSocket(
        'ws://' + window.location.host + 
        '/ws/canvas/' + canvasPK + '/collab/'
    );

    tagSocket = new WebSocket(
        'ws://' + window.location.host + 
        '/ws/canvas/' + canvasPK + '/tag/'
    );

/********************************************************************
*********************************************************************
                            CALLBACKS
*********************************************************************                            
*********************************************************************/
    
    /***********************************
                IDEA SOCKET
    ************************************/
    ideaSocket.onmessage = function(e){
        // console.log("Received");
        var data = JSON.parse(e.data);
        var f = data["function"];
        
        if (f.includes("typing")) {
            typingCallback(data, f);
            return;
        }
        switch(f) {
            case "modifyIdea": {
                editIdeaSuccessCallback(data);
                break;
            }
            case "addIdea": {
                var idea = data['idea'];
                newIdeaSuccessCallback(idea);
                break;
            }
            case "deleteIdea": {
                deleteIdeaSuccessCallback(data);
                break;
            }
        }


    };

    /***********************************
                COMMENT SOCKET
    ************************************/
    commentSocket.onmessage = function(e){
        var data = JSON.parse(e.data);
        var f = data["function"];

        switch(f) {
            case "addComment": {
                addCommentSuccessCallback(data);
                break;
            }
            case "deleteComment": {
                deleteCommentSuccessCallback(data);
                break;
            }
            case "resolveComments": {
                resolveCommentSuccessCallback(data);
                break;
            }
        }
    };

    /***********************************
                COLLAB SOCKET
    ************************************/
    collabSocket.onmessage = function(e){
        var data = JSON.parse(e.data);
        var f = data["function"];

        switch(f) {
            case "promoteUser": {
                promoteUserSuccessCallback(data);
                break;
            }
            case "demoteUser": {
                demoteAdminSuccessCallback(data);
                break;
            }
            case "addUser": {
                addUserSuccessCallback(data);
                break;
            }
            case "deleteUser": {
                deleteUserSuccessCallback(data);
                break;
            }
            case "newActiveUser": {
                newActiveUserCallback(data);
                break;
            }

            case "removeActiveUser": {
                removeActiveUserCallback(data);
                break;
            }

            case "sendWholeList": {
                wholeListCallback(data);
                break;
            }
        }
    };

    collabSocket.onopen = function(e){
        collabSocket.send(JSON.stringify({
            "function": "newActiveUser",
            "user": loggedInUser,
        }));
    };

    /***********************************
                TAG SOCKET
    ************************************/
    tagSocket.onmessage = function(e){
        var data = JSON.parse(e.data);
        var f = data["function"];

        switch(f) {
            case "addTag": {
                newTagSuccessCallback(data);
                break;
            }
            case "removeTag": {
                deleteTagSuccessCallback(data);
                break;
            }
        }
    };
}

function escapeHTMLChars(text){

    var string = escapeChars(text)
    // the following is to convert elements like &apos back to " ' " 
    var scratch = document.createElement("textarea")
    scratch.innerHTML = string
    return scratch.value
}

function setFalse(){
    this.isTyping = false;

    ideaSocket.send(JSON.stringify({
        'function': 'done_typing',
        'category': this.index,
        'username': loggedInUser[0].fields.username,
        'i': this.i

    }))
    window.clearTimeout(typingTimer)
    typingEntered = false;
    // console.log(typingEntered)
}   


function sortIdeas(inIdea, i, tempCategory){
    console.log(i);
    var prevIdea = inIdea;
    var currentIdea;
    var prevComments = sortedIdeas[tempCategory][i].comments;
    console.log(prevComments[0].fields.idea)
    console.log(prevIdea.pk)
    var currentComments;


    console.log(prevComments)

    for (var x = 0; x <= i; x++){
    /*
        Iterate through the list, shifting all elements to the right by one, until the
        modified idea is reached - this should not be shifted as everything after it
        will not have their order affected
    */  
        // need to hold on to the current idea temporarily as its current position in the array is to be used for the element before it
        currentIdea = sortedIdeas[tempCategory][x].idea;
        currentComments = sortedIdeas[tempCategory][x].comments;
        
        sortedIdeas[tempCategory].splice(x, 1, { 
            idea: prevIdea, 
            comments: prevComments
        });
        
        prevIdea = currentIdea;
        prevComments = currentComments;
    }
}

window.onbeforeunload = function(e){
    collabSocket.send(JSON.stringify({
            "function": "removeActiveUser",
            "user": loggedInUser,
    }));

    collabSocket.close();
    ideaSocket.close();
    tagSocket.close();
    commentSocket.close();
};

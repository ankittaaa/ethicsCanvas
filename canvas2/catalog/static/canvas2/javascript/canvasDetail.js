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

var thisCanvas;
var ideas;
// sortedIdeas will become a 2d array of objects. the 'i' indices will be the categories, while the  
// 'j' indices will be an object encapulating and idea and an array of its comments

var sortedIdeas = new Array(10);


var comments;
var tags = [];
var tagOccurrences = new Array();
var taggedCanvasses;
var admins;
var adminNames = [];
var users;

var loggedInUser
var publicCanvasses;
var privateCanvasses;
var selection;
var currentURL;
var isAdmin;

var tagButtons;
var collabComponent;
var ideaListComponent;

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
        "operation": "initialise"
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
    console.log(start);
    console.log(end);
    console.log(selection);
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

    // remove the victim {idea, [comments]} from the sorted ideas list
    var tempIdea = sortedIdeas[tempCategory][i].idea;
    for (t in tags){
        if (tempIdea.fields.text.includes(tags[t].fields.label))
            // decrement the tag if it occurs in the victim idea
            tagOccurrences[t]--;
        if (tagOccurrences[t] === 0){
            // delete the tag if it now does not occur 
            var thisTag = tags[t];
            data = {
                "tag_pk": thisTag.pk,
                "operation": "delete_tag"
            };
            performAjaxGET(currentURL, data, deleteTagSuccessCallback, deleteTagFailureCallback);
        }
    }

    sortedIdeas[tempCategory].splice(i, 1);

    ideaListComponent.ideaList = sortedIdeas;
    ideaListComponent.$children[0].$children[tempCategory].ideaList = sortedIdeas[tempCategory];
    
    // update every comment component inside the category
    for (i in sortedIdeas[tempCategory])
        ideaListComponent.$children[0].$children[tempCategory].$children[i].comments = sortedIdeas[tempCategory][i].comments;
}

function deleteIdeaFailureCallback(data){
    console.log("Deletion Failed");
}

function newIdeaSuccessCallback(data){
/*
    Function for updating the idea list for the modified category
    upon addition of new or deletion of current idea
*/
    var tempIdea = JSON.parse(data.idea);
    var tempCategory = tempIdea[0].fields.category;

    // since ideas are sorted from newest to oldest, push the new idea to the front of sortedIdeas for the category
    // and an empty array for the comments, as a brand-new idea has no comments yet    
    sortedIdeas[tempCategory].unshift({
        idea: tempIdea[0],
        comments: []
    });

    ideaListComponent.ideaList = sortedIdeas;
    ideaListComponent.$children[0].$children[tempCategory].ideaList = sortedIdeas[tempCategory];
    
    // update every comment component inside the category
    for (i in ideaListComponent.$children[0].$children[tempCategory].$children)
        ideaListComponent.$children[0].$children[tempCategory].$children[i].comments = sortedIdeas[tempCategory][i].comments;
}

function newIdeaFailureCallback(data){
    console.log(data);
}


function editIdeaSuccessCallback (data){

}

function editIdeaFailureCallback(data){
    console.log(data);
}

/*************************************************************************************************************
                                        COMMENT CALLBACKS
*************************************************************************************************************/


function addCommentSuccessCallback(data){
    populateCommentList(data);
}

function addCommentFailureCallback(data){
    console.log(data);
}


function deleteCommentSuccessCallback(data){
    populateCommentList(data);
}

function deleteCommentFailureCallback(data){
    console.log(data);
}


function resolveCommentSuccessCallback(data){
    var tempCategory = JSON.parse(data.category);
    var i = JSON.parse(data.i);

    // empty the comments for the idea
    sortedIdeas[tempCategory][i].comments = [];
    ideaListComponent.ideaList = sortedIdeas;
    
    ideaListComponent.$children[0].$children[tempCategory].$children[i].comments = [];

}
function resolveCommentFailureCallback(data){
    console.log(data);
}

/*************************************************************************************************************
                                            TAG CALLBACKS
*************************************************************************************************************/

function newTagSuccessCallback(data){
    // re-execute these steps so a new tag will, on being clicked, show it's in the current canvas
    tags = JSON.parse(data.tags);  
  
    taggedCanvasses = new Array(tags.length);
    publicCanvasses = JSON.parse(data.public);
    privateCanvasses = JSON.parse(data.private);

    var allCanvasses = JSON.parse(data.allCanvasses);

    populateTagList();
    tagButtons.tagList = tags
    tagButtons.canvasList = taggedCanvasses
}

function newTagFailureCallback(data){
    console.log(data.responseText);
}

function deleteTagSuccessCallback(data){
    var i = thisCanvas.fields.tags.indexOf(data);
    
    tagOccurrences.splice(i, 1);        
    thisCanvas.fields.tags.splice(i, 1);
    tags = thisCanvas.fields.tags;
}

function deleteTagFailureCallback(data){
    console.log(data.responseText);
}


/*************************************************************************************************************
                                        COLLABORATOR CALLBACKS
*************************************************************************************************************/

function addUserSuccessCallback(data){
    populateUsersAdmins(data);
}

function addUserFailureCallback(data){
    console.log(data.responseText);
}

function deleteUserSuccessCallback(data){
    populateUsersAdmins(data);
}

function deleteUserFailureCallback(data){
    console.log(data);
}

function promoteUserSuccessCallback(data){
    populateUsersAdmins(data);
}

function promoteUserFailureCallback(data){
    console.log(data.responseText);
}

function demoteAdminSuccessCallback(data){
    populateUsersAdmins(data);
}

function demoteAdminFailureCallback(data){
    console.log(data.responseText);
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
    }
    comments = JSON.parse(data.comments);
    ideas = JSON.parse(data.ideas);
    tags = JSON.parse(data.tags);
    
    admins = JSON.parse(data.admins);
    users = JSON.parse(data.users);
    loggedInUser = JSON.parse(data.loggedInUser);
    
    taggedCanvasses = new Array(tags.length);

    
    for (t in tags){
        tagOccurrences.push(0);
    }

    publicCanvasses = JSON.parse(data.public);
    privateCanvasses = JSON.parse(data.private);
    var allCanvasses = JSON.parse(data.allCanvasses);


    for (idea in ideas){
        var ideaComments = [];

        for (comment in comments){
            if (comments[comment].fields.idea === ideas[idea].pk){
                ideaComments.push(comments[comment]);
            }
        }

        for (t in tags){
            // keep track of how many times a tag occurs. on deletion of all ideas containing the tag, the occurrences reaches
            // 0 and the tag is removed 
            if (ideas[idea].fields.text.includes(tags[t].fields.label))
                tagOccurrences[t]++;
        }

        sortedIdeas[ideas[idea].fields.category].push({
            idea: ideas[idea],
            comments: ideaComments
        });
    }

    
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

    $j('#canvas-title').html(thisCanvas.fields.title);


    populateTagList();
    // populateIdeaList(); 

    tagButtons = new Vue({
        el: '#tag-div',
        data: {
            tagList: tags,
            canvasList: taggedCanvasses,
            show: false,
            showTag: true
        },
    })

    collabComponent = new Vue({
        el: '#collab-div',
        data: {
            showCollab: false,
            usersList: users,
            adminsList: admins,
            adminNameList: adminNames,
            loggedInUser: loggedInUser,
            isAdmin: isAdmin
        },
    })

    ideaListComponent = new Vue({
        el: '#idea-div',
        data: {
            ideaList: sortedIdeas,
            categories: categories,
        }
    })


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
        // console.log(this.ideaList)
    }
})

/*************************************************************************************************************
                                            IDEA-ELEM COMPONENT
*************************************************************************************************************/
 
Vue.component('idea', {
    props: ['ideas', 'index', 'categories'],
    delimiters: ['<%', '%>'],
    
    data: function(){
        return {
            showComments: false,
            // Array of booleans for displaying individual modal components. As a single boolean, all modals will be rendered instead of the one for the comment thread of the clicked idea. 
            showCommentThread: new Array(this.ideas.length)
        }
    },
    
    template:'  <div class="category-detail">\
                    <h3><% title() %></h3>\
                    <div v-for="(idea, i) in escapedIdeas">\
                    \
                    \
                        <input class="idea-input" type="text" :value="idea.fields.text" @change="changed($event, idea)" placeholder="Enter an idea">\
                        </br>\
                        <button id="delete-idea" class="delete" @click="deleteIdea($event, idea, i)">Delete</button>\
                        <button class="comments" v-on:click="displayMe(i)">Comments (<% commentList[i].length %>)</button>\
                        <comment v-show=showCommentThread[i] v-bind:commentList="commentList[i]" v-bind:idea="idea" v-bind:i="i" @close="displayMe(i)">\
                        </comment>\
                    </div>\
                    \
                    \
                    </br>\
                    <button class="new-idea" @click="newIdea($event)">+</button>\
                    <button class="new-tag" v-on:click="newTag()">Tag Selected Term</button>\
                    </br>\
                    </br>\
                </div>\
    ',
         
    computed: {
        category: function(){
            return this.ideaList[0].fields.category
        },

        ideaList: {
            get: function(){
                var list = []
                for (i in this.ideas){
                    list.push(this.ideas[i].idea)
                }
                return list
            },

            set: function(ideasInput){
                var list = []
                for (i in this.ideasInput){
                    list.push(this.ideasInput[i].idea)
                }
                return list
            },
        },

        commentList: function(){
            var list = []
            for (i in this.ideas){
                list.push(this.ideas[i].comments)
            }
            return list
        },
        /* 
            using computed property to escape the html characters such as &apos as vue throws an 
            "invalid assignment left-hand side" error when I call the method directly with v-model, 
            the error not appearing until @change is triggered   
        */ 
        escapedIdeas: function(){
            var escaped = this.ideaList

            for (idea in escaped){
                escaped[idea].fields.text = this.ideaString(escaped[idea])
            }
            return escaped
        },
    },
    
    watch: {
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

            for (c in comments){
                if (comments[c].fields.idea === idea.pk)
                {   
                    returnComments.push(comments[c])
                }
            }
            return returnComments
        },

        close: function(){
            this.showCommentThread = false
        },

        displayComments: function(event, idea){
            console.log(idea)
        },

        title: function(){
            return categories[this.category]
        },

        ideaString: function(idea){
            var string = escapeChars(idea.fields.text)
            // the following is to convert elements like &apos back to " ' " 
            var scratch = document.createElement("textarea")
            scratch.innerHTML = string

            return scratch.value
        },
        newIdea(event){
            var url = "/catalog/new_idea/"
            var data = {
                "canvas_pk": canvasPK,
                "category": this.category
            }
            performAjaxPOST(url, data, newIdeaSuccessCallback, newIdeaFailureCallback)
        },

        deleteIdea(event, idea, i){
            url = "/catalog/delete_idea/";
            data = {
                "idea_pk": idea.pk,
                'i': i
            };

            performAjaxPOST(url, data, deleteIdeaSuccessCallback, deleteIdeaFailureCallback);
        },

        changed(event, idea){
            var old = idea.fields.text
            var text = escapeChars(event.target.value)
            text = text.replace(/[\t\s\n\r]+/g, " ")
            text = text.trim()

            
            /* 
                if the new value is different to the old value after stripping
                tabs excess spaces, newlines and carriage returns, then the text
                has meaningfully changed and the database should be updated    
            */ 
            if(text !== old){
                var url = "/catalog/idea_detail/"
                data = {
                    "input_text": text,
                    "idea_pk": idea.pk
                }
                performAjaxPOST(url, data, editIdeaSuccessCallback, editIdeaFailureCallback);
            }
            // if a user entered loads of whitespace, then replace current input field with trimmed text
            event.target.value = text
            // does this maintain the new value?
            idea.fields.text = text
        },

        newTag(){
             data = {
                "canvas_pk": canvasPK,
                "operation": "add_tag",
                "tag": selection
            }
            performAjaxGET(currentURL, data, newTagSuccessCallback, newTagFailureCallback)
            selection = ""
        }

    },

    created: function(){
        for (var i = 0; i < this.showCommentThread.length; i++){
            this.showCommentThread[i] = false
        }
        // console.log(this.ideaList)
        // console.log(this.commentList)
    }
})

// TODO: Comment list and comment popup necessary?
/*************************************************************************************************************
                                            COMMENT-LIST COMPONENT
*************************************************************************************************************/
 
Vue.component('comment-list', {
    props: ['commentList', 'show-comment-thread'],
    delimiters: ['<%', '%>'],
    
    data: function(){
        return {
        }
    },
    
    template:'#comment-list',
         
    computed: {
    },
    
    watch: {

    },   

    methods: {

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
                        <input value = "" placeholder = "Type a comment" @change="newComment($event)">\
                        <button>Post</button>\
                    </div>\
                \
                \
                    <div slot="body">\
                        <ul>\
                            <li v-for="c in comments" style="list-style-type:none;">\
                                <% commentString(c) %>\
                                <button class="delete-comment" @click="deleteComment($event, c)">Delete</button>\
                            </li>\
                        </ul>\
                    </div>\
                \
                \
                    <div slot="footer">\
                        <button class="resolve-comments" @click="resolveComments(idea, comments)">Resolve All</button>\
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

    },   

    methods: {
        commentString: function(c){
            var string = escapeChars(c.fields.text)
            // the following is to convert elements like &apos back to " ' " 
            var scratch = document.createElement("textarea")
            scratch.innerHTML = string

            return scratch.value
        },

        newComment(event){
            var text = escapeChars(event.target.value)
            text = text.replace(/[\t\s\n\r]+/g, " ")
            text = text.trim()
            
            url = "/catalog/new_comment/"

            data = {
                "input_text": text,
                "idea_pk": this.currentIdea.pk,
                'i': this.selfIndex
            };
            performAjaxPOST(url, data, addCommentSuccessCallback, addCommentFailureCallback)
            event.target.value = ''
        },

        deleteComment(event, c){
            url = "/catalog/delete_comment/"

            data = {
                "comment_pk": c.pk,
                "idea_pk": this.currentIdea.pk,
                'i': this.selfIndex
            };
            performAjaxPOST(url, data, addCommentSuccessCallback, addCommentFailureCallback)
        },

        resolveComments(idea, comments){
            url = "/catalog/comment_resolve/"
            data = {
                "idea_pk": this.currentIdea.pk,
                'i': this.selfIndex,
            }
            performAjaxPOST(url, data, resolveCommentSuccessCallback, resolveCommentFailureCallback)
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
            performAjaxGET(currentURL, data, deleteTagSuccessCallback, deleteTagFailureCallback)
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
    props:['label', 'canvas'],
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
                    <button class="delete-tag" @click="$emit(\'delete-tag\')">Delete</button>\
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
            console.log(event.target)
            console.log(taggedCanvasses.indexOf(this.canvas))
        }
    }

})

/*************************************************************************************************************
                                            COLLAB-LIST COMPONENT
*************************************************************************************************************/
 
Vue.component('collabs', {
    template:'#collabs',

    data: function(){
        return {
            showCollab: false,
            usersList: users,
            adminsList: admins,
            adminNameList: adminNames,
            loggedInUser: loggedInUser,
            isAdmin: isAdmin,
        }
    },

    methods: {
    },
})

/*************************************************************************************************************
                                            COLLAB-POPUP COMPONENT
*************************************************************************************************************/
 
Vue.component('collab-popup', {
    props: ['users', 'admins', 'logged-in-user', 'is-admin', 'admin-names'],
    delimiters: ['<%', '%>'],

    data: function(){
        return {
            currentUser: this.loggedInUser,
            admin: this.isAdmin,
            name: '',
            a: '',
            c: ''
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
    },

    template: '\
            <modal>\
                <div slot="header">\
                    <h3>Collaborators</h3>\
                </div>\
                \
                <div slot="body">\
                    <h3>Admins</h3>\
                        <ul>\
                        <li v-for="a in adminList" style="list-style-type:none;">\
                            <% a.fields.username %>\
                            <div \
                                id="admin-buttons"\
                                v-if="loggedInUser[0].fields.username !== a.fields.username && admin === true"\
                            >\
                                <button class="delete-admin" @click="deleteUser($event, a)">Delete</button>\
                                <button class="demote-admin" @click="demoteAdmin($event, a)">Demote</button>\
                            </div>\
                        </li>\
                    </ul>\
                    \
                    <h3>Users</h3>\
                    <ul>\
                        <li v-for="u in userList" style="list-style-type:none;">\
                            <% u.fields.username %>\
                            <div \
                                id="user-buttons"\
                                v-if="loggedInUser[0].fields.username !== u.fields.username && admin === true"\
                            >\
                                <button class="delete-user" @click="deleteUser($event, u)">Delete</button>\
                                <button \
                                    v-if="adminNameList.indexOf(u.fields.username) === -1"\
                                    class="promote-user" @click="promoteUser($event, u)"\
                                >Promote</button>\
                            </div>\
                        </li>\
                    </ul>\
                </div>\
                \
                <div slot="footer">\
                    <h3>Add User</h3>\
                    <input v-model="name" placeholder="Enter a username">\
                    <button @click="addUser($event, name)">Add User</button>\
                    <button class="modal-default-button" @click="$emit(\'close\')">\
                    Close\
                    </button>\
                </div>\
            </modal>\
        ',

    methods: {
        addUser: function(event, name){
            var url = '/catalog/collaborators/'
            var data = {
                'name': name,
                'canvas_pk': canvasPK
            }
            // sending the POST request to a different URL to keep the view functions smaller. This isn't for redirection.
            performAjaxPOST(url, data, addUserSuccessCallback, addUserFailureCallback)
            this.name = ""
        },

        deleteUser: function(event, u){
            var url = "/catalog/delete_user/"
            var data = {
                'user_pk': u.pk,
                'canvas_pk': canvasPK
            }
            performAjaxPOST(url, data, deleteUserSuccessCallback, deleteUserFailureCallback)
        },

        promoteUser: function(event, u){
            var url = "/catalog/promote_user/"
            var data = {
                'user_pk': u.pk,
                'canvas_pk': canvasPK
            }
            performAjaxPOST(url, data, promoteUserSuccessCallback, promoteUserFailureCallback)
        },

        demoteAdmin: function(event, a){
            var url = "/catalog/demote_admin/"
            var data = {
                'user_pk': a.pk,
                'canvas_pk': canvasPK
            }
            performAjaxPOST(url, data, demoteAdminSuccessCallback, demoteAdminFailureCallback)
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

        taggedCanvasses[i] = tagged;

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


function populateCommentList(data){
/*
    Function to populate the comment lists of the idea list component and the 
    list of comments specific to the single comment component being updated
*/
    var tempIdea = JSON.parse(data.idea);
    var i = JSON.parse(data.i);
    var tempCategory = tempIdea[0].fields.category;
    var tempComments = JSON.parse(data.comments);
    // allComments = JSON.parse(data.allComments);

    sortedIdeas[tempCategory][i].comments = tempComments;
    ideaListComponent.ideaList = sortedIdeas;
    
    ideaListComponent.$children[0].$children[tempCategory].$children[i].comments = tempComments;
}

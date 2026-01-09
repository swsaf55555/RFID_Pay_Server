let token = localStorage.getItem("token") || "";
let students = [];
let filteredStudents = [];
let filteredSellers = [];
let sellers = [];
let currentPageStu = 1;
let currentPageSel = 1;
let pageSize = 10;
let popupCallback = null;
const API = "/api/admin";
const popupModal = new bootstrap.Modal(document.getElementById('popupModal'));

function jsonPost(url, data) {
    return fetch(url, {
        method: "POST",
        headers: {"Content-Type": "application/json", "Authorization": token ? "Bearer " + token : ""},
        body: JSON.stringify(data)
    }).then(r => r.json());
}

function login() {
    jsonPost(API + "/login", {
        username: document.getElementById("username").value,
        password: document.getElementById("password").value
    })
        .then(res => {
            if (res.code === 0) {
                token = res.data.token;
                localStorage.setItem("token", token);
                document.getElementById("main").classList.remove("hidden");
                document.getElementById("top-bar").classList.remove("hidden");
                document.getElementById("sidebar").classList.remove("hidden");
                document.getElementById("loginBox").style.display = "none";
                document.getElementById("main").style.display = "block";
                document.getElementById("top-bar").style.display = "flex";
                showSection("students")
                loadStudents();

            } else alert(res.msg);
        });
}

function loadStudents() {
    fetch(API + "/students", {headers: {"Authorization": "Bearer " + token}})
        .then(r => r.json()).then(res => {
        if (res.code !== 0) return alert(res.msg);
        students = res.data;
        filteredStudents = students;
        currentPageStu = 1;
        renderStudentTable();
    });
}

function renderStudentTable() {
    const tbody = document.querySelector("#studentTable tbody");
    tbody.innerHTML = "";
    const start = (currentPageStu - 1) * pageSize;
    const end = start + pageSize;
    filteredStudents.slice(start, end).forEach(s => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
      <td>${s.id}</td>
      <td>${s.student_no}</td>
      <td>${s.name}</td>
      <td>${s.card_id}</td>
      <td>${s.balance}</td>
      <td>${s.status ? "挂失" : "正常"}</td>
      <td>
        <button class="btn btn-success btn-sm me-1" onclick="openEditPopup(${s.id},'${s.name}','${s.card_id}','${s.balance}')">编辑</button>
        <button class="btn btn-primary btn-sm me-1" onclick="openRechargePopup('${s.card_id}','${s.name}')">充值</button>
        <button class="btn btn-danger btn-sm me-1" onclick="doLost('${s.card_id}')" style=${s.status?"display:none":""}>挂失</button>
        <button class="btn btn-secondary btn-sm" onclick="doUnlost('${s.card_id}')" style=${s.status?"":"display:none"}>解挂</button>
      </td>`;
        tbody.appendChild(tr);
    });
    document.getElementById("pageInfoStu").innerText = `第${currentPageStu}页 共${Math.ceil(filteredStudents.length / pageSize)}页`;
}

function prevPageStu() {
    if (currentPageStu > 1) {
        currentPageStu--;
        renderStudentTable();
    }
}

function nextPageStu() {
    if (currentPageStu < Math.ceil(filteredStudents.length / pageSize)) {
        currentPageStu++;
        renderStudentTable();
    }
}

function prevPageSel() {
    if (currentPageSel > 1) {
        currentPageSel--;
        renderSellerTable();
    }
}

function nextPageSel() {
    if (currentPageSel < Math.ceil(filteredSellers.length / pageSize)) {
        currentPageSel++;
        renderSellerTable();
    }
}

document.getElementById("searchInput").addEventListener("input", e => {
    const kw = e.target.value.trim().toLowerCase();
    filteredStudents = students.filter(s => s.name.toLowerCase().includes(kw) || s.student_no.toLowerCase().includes(kw)|| s.card_id.toLowerCase().includes(kw));
    currentPageStu = 1;
    renderStudentTable();
});

document.getElementById("searchInput-seller").addEventListener("input", e => {
    const kw = e.target.value.trim().toLowerCase();
    filteredSellers = sellers.filter(s => s.name.toLowerCase().includes(kw) || s.phone_number.toLowerCase().includes(kw)|| s.seller_name.toLowerCase().includes(kw)|| s.id.toString().toLowerCase().includes(kw));
    currentPageSel = 1;
    renderSellerTable();
});

window.addEventListener("load", function () {
    token = localStorage.getItem("token") || "";
    if (token) {

        jsonPost(API + "/login", {
        token: token
        })
        .then(res => {
            if (res.code === 0) {
                token = res.data.token;
                localStorage.setItem("token", token);
                document.getElementById("main").classList.remove("hidden");
                document.getElementById("top-bar").classList.remove("hidden");
                document.getElementById("sidebar").classList.remove("hidden");
                document.getElementById("loginBox").style.display = "none";
                document.getElementById("main").style.display = "block";
                document.getElementById("top-bar").style.display = "flex";
                showSection("students")
                loadStudents();

            } else {
                token = "";
                localStorage.removeItem("token");
                alert('登录已失效，请重新登录！');
            }
        });
    }
});


function openPopup(title, bodyHTML, callback) {
    document.getElementById("popupTitle").innerText = title;
    document.getElementById("popupBody").innerHTML = bodyHTML;
    popupCallback = callback;
    popupModal.show();
}

function closePopup() {
    popupModal.hide();
    popupCallback = null;
}

function submitPopup() {
    if (popupCallback) popupCallback();
}

function openAddPopup() {
    openPopup("新增学生", `
    <input id="pop_no" class="form-control mb-2" placeholder="学号"/>
    <input id="pop_name" class="form-control mb-2" placeholder="姓名"/>
    <input id="pop_card" class="form-control mb-2" placeholder="卡号"/>`,
        () => {
            jsonPost(API + "/student/add", {
                student_no: document.getElementById("pop_no").value,
                name: document.getElementById("pop_name").value,
                card_id: document.getElementById("pop_card").value
            }).then(res => {
                alert(res.msg);
                if (res.code === 0) {
                    closePopup();
                    loadStudents();
                }
            });
        });
}

function openEditPopup(id, name, card, balance) {
    openPopup("编辑学生", `
    <input id="pop_name" class="form-control mb-2" placeholder="姓名" value="${name}"/>
    <input id="pop_card" class="form-control mb-2" placeholder="卡号" value="${card}"/>
    <input id="pop_balance" class="form-control mb-2" placeholder="余额" value="${balance}"/>`,
        () => {
            jsonPost(API + "/student/edit", {
                id: id,
                name: document.getElementById("pop_name").value,
                balance: document.getElementById("pop_balance").value,
                card: document.getElementById("pop_card").value
            })
                .then(res => {
                    alert(res.msg);
                    if (res.code === 0) {
                        closePopup();
                        loadStudents();
                    }
                });
        });
}

function openRechargePopup(card_id, name) {
    openPopup("充值 - " + name, `
    <input id="pop_amount" class="form-control mb-2" placeholder="充值金额"/>`,
        () => {
            const amount = document.getElementById("pop_amount").value;
            jsonPost("/api/card/recharge", {card_id, amount})
                .then(res => {
                    window.open(res.pay_url, "_blank");
                    alert('您的订单号：'+res.out_trade_no+'，请勿重复发起支付。');
                    closePopup();
                    loadStudents();
                });
        });
}


function doLost(card_id) {
    jsonPost(API + "/student/lost", {card_id}).then(res => {
        alert(res.msg);
        if (res.code === 0) loadStudents();
    });
}

function doUnlost(card_id) {
    jsonPost(API + "/student/unlost", {card_id}).then(res => {
        alert(res.msg);
        if (res.code === 0) loadStudents();
    });
}

function doBan(id) {
    jsonPost(API + "/seller/ban", {id}).then(res => {
        alert(res.msg);
        if (res.code === 0) loadSellers();
    });
}

function doActive(id) {
    jsonPost(API + "/seller/active", {id}).then(res => {
        alert(res.msg);
        if (res.code === 0) loadSellers();
    });
}

function logout() {
    jsonPost(API + "/logout").then(res => {
        alert(res.msg);
        if (res.code === 0) {
            token = "";
            localStorage.removeItem("token");
            window.location.reload()
        }
    })

}

function checkEnter(e) {
    if (e.key === "Enter") {
        login();
    }
}


function toggleSidebar() {
    const sidebar = document.getElementById("sidebar");
    sidebar.style.display = sidebar.style.display === "none" ? "block" : "none";
}

function showSection(section) {
    document.getElementById("studentsSection").classList.add("hidden");
    document.getElementById("sellersSection").classList.add("hidden");
    document.getElementById(section + "Section").classList.remove("hidden");

    document.getElementById('student-a').classList.remove("menu-active");
    document.getElementById('seller-a').classList.remove("menu-active");

    if (section === "students") {
        document.getElementById('student-a').classList.add("menu-active");
        loadStudents();
    } else {
        document.getElementById('seller-a').classList.add("menu-active");
        loadSellers();
    }
}

// function loadStudents() {
//     fetch(API + "/students", {headers: {"Authorization": "Bearer " + token}})
//         .then(r => r.json()).then(res => {
//         if (res.code !== 0) return alert(res.msg);
//         students = res.data;
//         filteredStudents = students;
//         currentPage = 1;
//         renderStudentTable();
//     });
// }
function loadSellers() {
    fetch(API + "/sellers", {headers: {"Authorization": "Bearer " + token}})
        .then(r => r.json()).then(res => {
            if(res.code !== 0) return alert(res.msg);
            sellers = res.data;
            filteredSellers = sellers;
            currentPageSel=1;
            renderSellerTable();
        });
}
// function renderStudentTable() {
//     const tbody = document.querySelector("#studentTable tbody");
//     tbody.innerHTML = "";
//     const start = (currentPage - 1) * pageSize;
//     const end = start + pageSize;
//     filtered.slice(start, end).forEach(s => {
//         const tr = document.createElement("tr");
//         tr.innerHTML = `
//       <td>${s.id}</td>
//       <td>${s.student_no}</td>
//       <td>${s.name}</td>
//       <td>${s.card_id}</td>
//       <td>${s.balance}</td>
//       <td>${s.status ? "挂失" : "正常"}</td>
//       <td>
//         <button class="btn btn-success btn-sm me-1" onclick="openEditPopup(${s.id},'${s.name}','${s.card_id}','${s.balance}')">编辑</button>
//         <button class="btn btn-primary btn-sm me-1" onclick="openRechargePopup('${s.card_id}','${s.name}')">充值</button>
//         <button class="btn btn-danger btn-sm me-1" onclick="doLost('${s.card_id}')" style=${s.status?"display:none":""}>挂失</button>
//         <button class="btn btn-secondary btn-sm" onclick="doUnlost('${s.card_id}')" style=${s.status?"":"display:none"}>解挂</button>
//       </td>`;
//         tbody.appendChild(tr);
//     });
//     document.getElementById("pageInfo").innerText = `第${currentPage}页 共${Math.ceil(filtered.length / pageSize)}页`;
// }
function renderSellerTable() {
    const tbody = document.querySelector("#sellerTable tbody");
    tbody.innerHTML = "";
    const start = (currentPageSel - 1) * pageSize;
    const end = start + pageSize;
    filteredSellers.slice(start, end).forEach(s => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
        <td>${s.id}</td>
        <td>${s.name}</td>
        <td>${s.seller_name}</td>
        <td>${s.phone_number}</td>
        <td>${s.balance}</td>
        <td>${s.status ? "停用" : "正常"}</td>
        <td>
          <button class="btn btn-primary btn-sm" onclick="openEditSellerPopup(${s.id},'${s.name}','${s.seller_name}','${s.phone_number}',${s.balance})">编辑</button>
          <button class="btn btn-primary btn-sm" onclick="openEditPasswdSellerPopup(${s.id})">修改密码</button>
          <button class="btn btn-danger btn-sm me-1" onclick="doBan('${s.id}')" style=${s.status?"display:none":""}>停用</button>
          <button class="btn btn-secondary btn-sm" onclick="doActive('${s.id}')" style=${s.status?"":"display:none"}>启用</button>
        </td>`;
        tbody.appendChild(tr);
    });
    document.getElementById("pageInfoSel").innerText = `第${currentPageSel}页 共${Math.ceil(filteredSellers.length / pageSize)}页`;
}

function openAddSellerPopup() {
    openPopup("新增卖家", `
        <input id="pop_seller_name" class="form-control mb-2" placeholder="姓名"/>
        <input id="pop_seller_seller_name" class="form-control mb-2" placeholder="商户名"/>
        <input id="pop_seller_phone" class="form-control mb-2" placeholder="手机号"/>
        <input id="pop_seller_password" class="form-control mb-2" placeholder="密码"/>
        <input id="pop_seller_balance" class="form-control mb-2" placeholder="初始余额" value="0.00"/>`,
        () => {
            jsonPost(API + "/seller/add", {
                name: document.getElementById("pop_seller_name").value,
                seller_name: document.getElementById("pop_seller_seller_name").value,
                phone_number: document.getElementById("pop_seller_phone").value,
                password: document.getElementById("pop_seller_password").value,
                balance: document.getElementById("pop_seller_balance").value
            }).then(res => {
                alert(res.msg);
                if(res.code === 0) {
                    closePopup();
                    loadSellers();
                }
            });
        }
    );
}

function openEditPasswdSellerPopup(id) {
    openPopup("修改商家密码", `
        <input id="pop_seller_password_old" class="form-control mb-2" placeholder="旧密码" type="password" required/>
        <input id="pop_seller_password_new" class="form-control mb-2" placeholder="新密码" type="password" required/>
        <input id="pop_seller_password_retry" class="form-control mb-2" placeholder="验证新密码" type="password" required/>`,
        () => {
            if(document.getElementById("pop_seller_password_new").value
                ===
                document.getElementById("pop_seller_password_retry").value){
                jsonPost(API + "/seller/passwd", {
                id: id,
                passwd_old: document.getElementById("pop_seller_password_old").value,
                passwd_new: document.getElementById("pop_seller_password_new").value}
                ).then(res => {
                    alert(res.msg);
                    if (res.code === 0) {
                        closePopup();
                        loadSellers();
                    }
                });
            }else{
                alert('两次新密码输入不一致！')
            }
        });
}

function openEditSellerPopup(id, name, seller_name,phone_number,balance) {
    openPopup("编辑商家", `
        <input id="pop_seller_name" class="form-control mb-2" placeholder="姓名" value="${name}"/>
        <input id="pop_seller_seller_name" class="form-control mb-2" placeholder="商户名" value="${seller_name}"/>
        <input id="pop_seller_phone" class="form-control mb-2" placeholder="手机号" value="${phone_number}"/>
        <input id="pop_seller_balance" class="form-control mb-2" placeholder="余额（慎重修改）" value="${balance}"/>`,
        () => {
            jsonPost(API + "/seller/edit", {
                id: id,
                name: document.getElementById("pop_seller_name").value,
                seller_name: document.getElementById("pop_seller_seller_name").value,
                phone_number: document.getElementById("pop_seller_phone").value,
                balance: document.getElementById("pop_seller_balance").value
            })
                .then(res => {
                    alert(res.msg);
                    if (res.code === 0) {
                        closePopup();
                        loadSellers();
                    }
                });
        });
}

function openEditAdminPasswdPopup() {
    openPopup("修改管理员密码", `
        <input id="pop_admin_password_old" class="form-control mb-2" placeholder="旧密码" type="password" required/>
        <input id="pop_admin_password_new" class="form-control mb-2" placeholder="新密码" type="password" required/>
        <input id="pop_admin_password_retry" class="form-control mb-2" placeholder="验证新密码" type="password" required/>`,
        () => {
            if(document.getElementById("pop_admin_password_new").value
                ===
                document.getElementById("pop_admin_password_retry").value){
                jsonPost(API + "/passwd", {
                passwd_old: document.getElementById("pop_admin_password_old").value,
                passwd_new: document.getElementById("pop_admin_password_new").value}
                ).then(res => {
                    alert(res.msg);
                    if (res.code === 0) {
                        closePopup();
                        window.location.reload();
                    }
                });
            }else{
                alert('两次新密码输入不一致！')
            }
        });
}
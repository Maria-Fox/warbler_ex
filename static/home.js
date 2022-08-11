let mess_form = document.getElementsByClassName("fa fa-thumbs-up");
console.log(mess_form);

async function handle_like(e) {
  e.preventDefault();

  message_id = document.getElementById();
  const response = await axios.post(`/messages/<int:message_id>/like`);
  console.log(response);
}

// mess_form.addEventListener("click", handle_like);

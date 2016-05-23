var UserItem = React.createClass({
  sec2Date: function(sec) {
    let dt = new Date(sec * 1000);
    return dt.getFullYear() + '/' + (dt.getMonth() + 1) + '/' + dt.getDate();
  },
  render: function() {
    return (
      <tr>
        <td>{this.props.name}</td>
        <td>{this.props.email}</td>
        <td>{this.sec2Date(this.props.createdAt)}</td>
        <td>{this.props.admin ? 'Yes' : 'No'}</td>
      </tr>
    );
  }
});

var UserList = React.createClass({
  render: function() {
    return (
      <table id="userList" className="table table-striped">
        <thead>
          <tr>
            <th>Name</th>
            <th>Email</th>
            <th>Join at</th>
            <th>Admin</th>
          </tr>
        </thead>
        <tbody>
        {
          this.props.users.map(function(user) {
            return (
              <UserItem name={user.name} email={user.email} admin={user.admin} createdAt={user.created_at} key={user.id} />
            );
          })
        }
        </tbody>
      </table>
    );
  }
});

var UserControlPanel = React.createClass({
  updateState: function(data) {
    this.setState({
      page: data.page,
      users: data.users,
      userCount: data.user_count,
      pageSize: data.page_size,
      pageCount: data.page_count
    });
  },
  getNext: function(e) {
    e.preventDefault();
    if(this.state.page >= this.state.pageCount) return;
    $.ajax({
      url: this.props.url,
      dataType: 'json',
      data: {
        page: this.state.page + 1
      },
      success: function(data) {
        this.updateState(data);
      }.bind(this),
      error: function(xhr, status, err) {
        console.error('error:', this.props.url, status, err.toString());
      }.bind(this)
    });
  },
  getPrev: function(e) {
     e.preventDefault();
     if(this.state.page === 1) return;
     $.ajax({
       url: this.props.url,
       dataType: 'json',
       data: {
         page: this.state.page - 1,
       },
       success: function(data) {
         this.updateState(data);
       }.bind(this),
       error: function(xhr, status, err) {
         console.error('error:', this.props.url, status, err.toString());
       }.bind(this)
     });
  },
  getInitialState: function() {
    return {
      page: 1,
      users: [],
      userCount: 0,
      pageSize: 10,
      pageCount: 1
    };
  },
  componentDidMount: function() {
    $.ajax({
      url: this.props.url,
      dataType: 'json',
      data: {
        page: this.state.page
      },
      success: function(data) {
         this.updateState(data);
      }.bind(this),
      error: function(xhr, status, err) {
        console.error('error:', this.props.url, status, err.toString());
      }.bind(this)
    });
  },
  render: function() {
    return (
      <div>
        <UserList users={this.state.users}/>
        <nav>
          <ul className="pager">
            <li className={'previous' + (this.state.page > 1 ? '' : ' disabled')} onClick={this.getPrev}><a role="button"><span aria-hidden="true">&larr;</span></a></li>
            <li className={'next' + (this.state.page < this.state.pageCount ? '' : ' disabled')} onClick={this.getNext}><a role="button"><span aria-hidden="true">&rarr;</span></a></li>
          </ul>
        </nav>
      </div>
    );
  }
});

ReactDOM.render(
   <UserControlPanel url="/api/users" />,
   $('#contentBody')[0]
);

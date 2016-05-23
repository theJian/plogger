var BlogItem = React.createClass({
  sec2Date: function(sec) {
    let dt = new Date(sec * 1000);
    return dt.getFullYear() + '/' + (dt.getMonth() + 1) + '/' + dt.getDate();
  },
  render: function() {
    return (
        <tr>
          <td>{this.props.title}</td>
          <td>{this.props.author}</td>
          <td>{this.sec2Date(this.props.createdAt)}</td>
          <td>
            <div className="btn-group" role="group">
              <button type="button" className="btn btn-default" onClick={this.props.onClickDelete}><span className="glyphicon glyphicon-trash" aria-hidden="true"></span> delete </button> <button type="button" className="btn btn-default" onClick={this.props.onClickEdit}><span className="glyphicon glyphicon-pencil" aria-hidden="true"></span> edit </button>
            </div>
          </td>
        </tr>
        );
  }
});

var BlogList = React.createClass({
  render: function() {
    const onClickEdit = this.props.onClickEdit;
    const onClickDelete = this.props.onClickDelete;
    return (
        <table id="blogList" className="table table-striped">
          <thead>
            <tr>
              <th>Title</th>
              <th>Author</th>
              <th>Created At</th>
              <th>Operations</th>
            </tr>
          </thead>
          <tbody>
          {
            this.props.blogs.map(function(blog) {
              return <BlogItem title={blog.name} author={blog.user_name} createdAt={blog.created_at} key={blog.id} onClickEdit={onClickEdit.bind(null, blog.id)} onClickDelete={onClickDelete.bind(null, blog.id)}/>;
            })
          }
          </tbody>
        </table>
        );
  }
});

var BlogControlPanel = React.createClass({
  updateState: function(data) {
    this.setState({
      page: data.page,
      blogs: data.blogs,
      blogCount: data.blog_count,
      pageSize: data.page_size,
      pageCount: data.page_count
    });
  },
  jumpToComposePage: function() {
    window.location = '/manage/blogs/editor';
  },
  onClickEdit: function(id) {
    window.location = '/manage/blogs/editor?' + $.param({id:id});
  },
  onClickDelete: function(id) {
    $.ajax({
      type: 'POST',
      url: '/api/blogs/delete',
      data: {
        id: id
      },
      success: function(data) {
        this.setState({blogs: this.state.blogs.filter(blog => blog.id !== id)});
      }.bind(this),
      error: function(xhr, status, err) {
        console.error('error:', this.props.url, status, err.toString());
      }.bind(this)
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
      blogs: [],
      blogCount: 0,
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
          <button type="button" className="btn btn-default" onClick={this.jumpToComposePage}>Compose</button>
          <BlogList blogs={this.state.blogs} onClickEdit={this.onClickEdit} onClickDelete={this.onClickDelete}/>
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
  <BlogControlPanel url="/api/blogs" />,
  $('#contentBody')[0]
);

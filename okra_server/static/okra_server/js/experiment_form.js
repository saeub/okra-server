Vue.component("experiment-form", {
  template: `
    <ul>
      <li>ID: <input type="text" v-model="data.id" @input="emitData()" disabled></li>
      <li>
        Task type:
        <select v-model="data.taskType" @input="emitData()">
          <option v-for="(typeName, typeId) in taskTypeChoices" :value="typeId">
            {{ typeName }}
          </option>
        </select>
      </li>
      <li>Title: <input type="text" v-model="data.title" @input="emitData()"></li>
      <li>Instructions: <textarea v-model="data.instructions" @input="emitData()"></textarea></li>
      <li>
        Practice task:
        <input type="checkbox" v-model="hasPracticeTask">
        <task v-if="data.practiceTask !== null" v-model="data.practiceTask" @input="emitData()"></task>
      </li>
      <li>
        Tasks:
        <ul>
          <li v-for="(task, i) in data.tasks" :key="'task-' + task.key">
            <input type="button" value="Remove task" @click="removeTask(i)">
            <task v-model="data.tasks[i]"></task>
          </li>
        </ul>
        <input type="button" value="Add task" @click="addTask()">
      </li>
      <li>
        Task ratings:
        <ul>
          <li v-for="(rating, i) in data.ratings" :key="'rating-' + rating.key">
            <input type="button" value="Remove rating" @click="removeRating(i)">
            <rating :rating-type-choices="ratingTypeChoices" v-model="data.ratings[i]"></rating>
          </li>
        </ul>
        <input type="button" value="Add rating" @click="addRating()">
      </li>
      <li>
        Assignments:
        <ul>
          <li v-for="assignment in data.assignments" :key="'participant-' + assignment.participant">
            <task-assignments :participant="assignment.participant" :tasks="data.tasks" v-model="assignment.tasks"></task-assignments>
          </li>
        </ul>
      </li>
    </ul>
  `,

  props: {
    value: {
      type: Object,
      required: true,
    },
    taskTypeChoices: {
      type: Object,
      required: true,
    },
    ratingTypeChoices: {
      type: Object,
      required: true,
    },
  },

  data() {
    const data = { ...this.value };
    const hasPracticeTask = data.practiceTask !== null;
    let taskKeyCounter = 0;
    for (task of data.tasks) {
      task.key = taskKeyCounter;
      taskKeyCounter++;
    }
    let ratingKeyCounter = 0;
    for (rating of data.ratings) {
      rating.key = ratingKeyCounter;
      ratingKeyCounter++;
    }
    return {
      data: { ...this.value },
      taskKeyCounter,
      ratingKeyCounter,
      hasPracticeTask,
    };
  },

  methods: {
    addTask() {
      this.data.tasks.push({
        id: uuidv4(),
        key: this.taskKeyCounter,
        label: `task-${this.taskKeyCounter}`,
        data: {},
      });
      this.taskKeyCounter++;
      this.emitData();
    },

    removeTask(index) {
      this.data.tasks.splice(index, 1);
      this.emitData();
    },

    addRating() {
      this.data.ratings.push({
        id: uuidv4(),
        key: this.ratingKeyCounter,
        question: "",
        type: "emoticon",
        lowExtreme: null,
        highExtreme: null,
      });
      this.ratingKeyCounter++;
      this.emitData();
    },

    removeRating(index) {
      this.data.ratings.splice(index, 1);
      this.emitData();
    },

    emitData() {
      this.$emit("input", this.data);
    },
  },

  watch: {
    hasPracticeTask(newHasPracticeTask) {
      if (newHasPracticeTask) {
        this.data.practiceTask = {
          id: uuidv4(),
          label: `practice-task`,
          data: {},
        };
      } else {
        this.data.practiceTask = null;
      }
      this.emitData();
    },
  },
});

Vue.component("task", {
  template: `
    <ul>
      <li>ID: <input type="text" v-model="task.id" @input="emitData()" disabled></li>
      <li>Label: <input type="text" v-model="task.label" @input="emitData()"></li>
      <li>Data: <json-editor v-model="task.data" @input="emitData()"></json-editor></li>
    </ul>
  `,

  props: {
    value: {
      type: Object,
      required: true,
    },
  },

  data() {
    return {
      task: { ...this.value },
    };
  },

  methods: {
    emitData() {
      this.$emit("input", this.task);
    },
  },
});

Vue.component("rating", {
  template: `
    <ul>
      <li>ID: <input type="text" v-model="rating.id" @input="emitData()" disabled></li>
      <li>Question: <input type="text" v-model="rating.question" @input="emitData()"></li>
      <li>
        Type:
        <select v-model="rating.type" @input="emitData()">
          <option v-for="(typeName, typeId) in ratingTypeChoices" :value="typeId">
            {{ typeName }}
          </option>
        </select>
      <li>Low extreme: <input type="text" v-model="rating.lowExtreme" @input="emitData()"></li>
      <li>High extreme: <input type="text" v-model="rating.highExtreme" @input="emitData()"></li>
    </ul>
  `,

  props: {
    value: {
      type: Object,
      required: true,
    },
    ratingTypeChoices: {
      type: Object,
      required: true,
    },
  },

  data() {
    return {
      rating: { ...this.value },
    };
  },

  methods: {
    emitData() {
      this.$emit("input", this.rating);
    },
  },
});

Vue.component("json-editor", {
  template: `
    <div>
      <textarea v-model="text" @input="validate()">{{ text }}</textarea>
      <div v-if="error !== null" style="color: red">
        {{ error }}
      </div>
      <div v-else style="color: green">
        Valid.
      </div>
    </div>
  `,

  props: {
    value: {
      type: undefined,
      required: true,
    },
  },

  data() {
    return {
      text: JSON.stringify(this.value),
      error: null,
    };
  },

  methods: {
    validate() {
      try {
        const data = JSON.parse(this.text);
        this.error = null;
        this.$emit("input", data);
      } catch (e) {
        this.error = e;
      }
    },
  },
});

Vue.component("task-assignments", {
  template: `
    <div>
      {{ participant }}
      <select v-for="(assignment, i) in assignments" :value="assignments[i].id" @input="onInput(i, $event.target.value)">
        <option value="DELETED">- DELETE -</option>
        <option v-for="task in tasks" :key="task.id" :value="task.id">{{ task.label }}</option>
      </select>
      <input type="button" value="+" @click="addTask()" :disabled="getAvailableAssignment() === null">
    </div>
  `,

  props: {
    participant: {
      type: String,
      required: true,
    },
    tasks: {
      type: Array,
      required: true,
    },
    value: {
      type: Array,
      required: true,
    },
  },

  data() {
    return {
      assignments: [...this.value],
    };
  },

  methods: {
    getAvailableAssignment() {
      for (const task of this.tasks) {
        var taken = false;
        for (const assignment of this.assignments) {
          if (assignment.id == task.id) {
            taken = true;
            break;
          }
        }
        if (!taken) {
          return {
            id: task.id,
            started: false,
          };
        }
      }
      return null;
    },

    addTask() {
      const availableAssignment = this.getAvailableAssignment();
      console.log(availableAssignment);
      if (availableAssignment !== null) {
        this.assignments.push(availableAssignment);
      }
      this.emitData();
    },

    onInput(index, value) {
      if (value === "DELETED") {
        this.assignments.splice(index, 1);
      } else {
        this.assignments[index] = { id: value, started: false };
      }
      console.log(this.assignments);
      this.emitData();
    },

    emitData() {
      this.$emit("input", this.assignments);
    },
  },

  watch: {
    tasks(newTasks) {
      const newTaskIds = [];
      for (task of newTasks) {
        newTaskIds.push(task.id);
      }
      for (let i = 0; i < this.assignments.length; i++) {
        if (newTaskIds.indexOf(this.assignments[i].id) === -1) {
          this.assignments.splice(i, 1);
          i--;
        }
      }
      this.emitData();
    },
  },
});

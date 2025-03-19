/**
 * A basic particle simulator that simulates a short-range 1/r^2
 * repulsive force between particles in an enclosed 2D space.

 * This code is based on the particle simulation project in CS267 at
 * UC Berkeley.
 */

///////////////////////
// Simulation Values //
///////////////////////

int num_particles() {
  return 20;
}

int num_steps() {
  return 10;
}

double box_size() {
  return 0.1;
}

double[] initial_x_positions() {
  return new double[]{0.0167, 0.033, 0.05, 0.0667, 0.0833, 0.0167, 0.033,
                      0.05, 0.0667, 0.0833, 0.0167, 0.033, 0.05, 0.0667,
                      0.0833, 0.0167, 0.033, 0.05, 0.0667, 0.0833};
}

double[] initial_y_positions() {
  return new double[]{0.02, 0.02, 0.02, 0.02, 0.02, 0.04, 0.04, 0.04,
                      0.04, 0.04, 0.06, 0.06, 0.06, 0.06, 0.06, 0.08,
                      0.08, 0.08, 0.08, 0.08};
}

double[] initial_x_velocities() {
  return new double[]{-0.482, 0.430, -0.338, -0.556, -0.332, 0.880,
                      -0.730, 0.458, 0.576, 0.792, -0.810, -0.836,
                      0.572, -0.038, -0.960, 0.872, 0.704, -0.35,
                      -0.374, -0.348};
}

double[] initial_y_velocities() {
  return new double[]{-0.330, -0.622, 0.088, -0.058, 0.328, 0.292,
                      0.792, 0.648, 0.812, -0.460, -0.382, -0.624,
                      0.262, -0.662, -0.212, 0.914, -0.898, -0.026,
                      -0.062, 0.008};
}

/////////////////////////////
// Particle Representation //
/////////////////////////////

double density() {
  return 0.0005;
}

double mass() {
  return 0.01;
}

// prevent very large forces due to discretization/fp inaccuracy
double cutoff_radius() {
  return 0.01;
}

double min_radius_squared() {
  return pow(cutoff_radius() / 100, 2);
}

double time_interval() {
  return 0.0005;
}

// A particle in the simulation. A particle has a 2D position,
// velocity, and acceleration, and a unique ID.
struct particle {
  double x;
  double y;
  double x_vel;
  double y_vel;
  double x_acc;
  double y_acc;
  int id;
};

double max(double a, double b) {
  if (a > b) {
    return a;
  }
  return b;
}

// Apply a simple short-range repulsive force from another particle.
void apply_force(particle p, particle other) {
  double dx = other.x - p.x;
  double dy = other.y - p.y;
  if (dx == 0 && dy == 0) {
    // no directional force from particle at same location
    return;
  }

  double radius2 = max(dx * dx + dy * dy, min_radius_squared());
  if (radius2 > cutoff_radius() * cutoff_radius()) {
    // out of force range
    return;
  }
  double radius = sqrt(radius2);

  // Very simple short-range repulsive force
  double coefficient = (1 - cutoff_radius() / radius) / radius2 / mass();
  p.x_acc = p.x_acc + coefficient * dx;
  p.y_acc = p.y_acc + coefficient * dy;
}


// Move a particle for one timestep. Slightly simplified Velocity
// Verlet integration conserves energy better than explicit Euler
// method.
void move_particle(particle p) {
  assert p.x >= 0 && p.x <= box_size() : "invalid x position: " + p.x;
  assert p.y >= 0 && p.y <= box_size() : "invalid y position: " + p.y;
  p.x_vel = p.x_vel + p.x_acc * time_interval();
  p.y_vel = p.y_vel + p.y_acc * time_interval();
  p.x = p.x + p.x_vel * time_interval();
  p.y = p.y + p.y_vel * time_interval();

  // Bounce from walls
  while (p.x < 0 || p.x > box_size()) {
    if (p.x < 0) {
      p.x = -p.x;
    } else {
      p.x = 2 * box_size() - p.x;
    }
    p.x_vel = -p.x_vel;
  }
  while (p.y < 0 || p.y > box_size()) {
    if (p.y < 0) {
      p.y = -p.y;
    } else {
      p.y = 2 * box_size() - p.y;
    }
    p.y_vel = -p.y_vel;
  }
}

// Print the position of each particle.
void print_particle_positions(particle[] ps) {
  for (int i = 0; i < ps.length; ++i) {
    println(ps[i].id + ": " + ps[i].x + ", " + ps[i].y);
  }
  println("");
}

////////////////////
// Initialization //
////////////////////

// Construct an array of num_particles particles in two dimensions,
// with initial positions and velocities as specified by the
// simulation values above.
particle[] make_particles(int num_particles) {
  assert num_particles > 0;
  particle[] particles = new particle[]{};
  double[] xs = initial_x_positions();
  double[] ys = initial_y_positions();
  double[] xvs = initial_x_velocities();
  double[] yvs = initial_y_velocities();
  for (int i = 0; i < num_particles; ++i) {
    particles << new particle(xs[i], ys[i], xvs[i], yvs[i], 0, 0, i);
  }
  return particles;
}

///////////////////////
// Simulation Driver //
///////////////////////

// Simulate num_particles() particles for num_steps steps.
void simulate(int num_steps) {
  // Create particles
  particle[] particles = make_particles(num_particles());

  println("Initial");
  print_particle_positions(particles);

  // Perform simulation
  for (int step = 0; step < num_steps; ++step) {
    println("Step " + (step + 1));

    // Compute forces
    for (int i = 0; i < num_particles(); ++i) {
      // reset acceleration to 0
      particles[i].x_acc = 0;
      particles[i].y_acc = 0;
      // now apply forces from other particles
      for (int j = 0; j < num_particles(); ++j) {
        apply_force(particles[i], particles[j]);
      }
    }

    // Move particles
    for (int i = 0; i < num_particles(); ++i) {
      move_particle(particles[i]);
    }

    // Print particle positions
    print_particle_positions(particles);
  }
}

//////////////////////////

void main(string[] args) {
  if (args.length > 0) {
    simulate(string_to_int(args[0]));
  } else {
    simulate(num_steps());
  }
}
